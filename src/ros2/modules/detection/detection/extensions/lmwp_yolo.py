"""
LMWP-YOLO Architecture Extensions

This module contains custom neural network blocks for the LMWP-YOLO architecture,
designed for long-range drone detection in challenging conditions.

Reference: "Improved YOLO for long range detection of small drones" - Nature Scientific Reports

Main Components:
- MAFR: Multi-scale Adaptive Feature Refinement (core detection module)
- PP-LCNet Backbone: Lightweight CPU-optimized backbone stages
- Attention Mechanisms: MCALayer, SimAM, GAMAttention, CoordAtt, ECA, SE

These blocks extend ultralytics YOLO with specialized components for small object detection.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math

__all__ = [
    # Core LMWP-YOLO modules
    'MAFR', 'MCALayer', 'LightweightMSFFM', 'MiniResidualBlock',
    # Attention mechanisms
    'SimAM', 'GAMAttention', 'SE', 'CoordAtt', 'ECA', 'SELayer',
    # Supporting modules
    'MCAGate', 'StdPool', 'h_sigmoid', 'h_swish', 'channel_shuffle',
    # PP-LCNet backbone
    'PPLCNetStem', 'PPLCNetStage', 'PPLCNetStage1', 'PPLCNetStage2',
    'PPLCNetStage3', 'PPLCNetStage4', 'HardSwish', 'DepthSepConv'
]


# ============================================================================
# Activation Functions
# ============================================================================

class h_sigmoid(nn.Module):
    """Hard sigmoid activation - efficient approximation of sigmoid"""
    def __init__(self, inplace=True):
        super(h_sigmoid, self).__init__()
        self.relu = nn.ReLU6(inplace=inplace)

    def forward(self, x):
        return self.relu(x + 3) / 6


class h_swish(nn.Module):
    """Hard swish activation - efficient approximation of swish"""
    def __init__(self, inplace=True):
        super(h_swish, self).__init__()
        self.sigmoid = h_sigmoid(inplace=inplace)

    def forward(self, x):
        return x * self.sigmoid(x)


class HardSwish(nn.Module):
    """H-Swish activation (efficient for mobile/CPU)"""
    def __init__(self, inplace=True):
        super().__init__()
        self.inplace = inplace

    def forward(self, x):
        return x * F.relu6(x + 3., inplace=self.inplace) / 6.


def channel_shuffle(x, groups=2):
    """Shuffle channels for grouped convolution"""
    B, C, H, W = x.size()
    out = x.view(B, groups, C // groups, H, W).permute(0, 2, 1, 3, 4).contiguous()
    out = out.view(B, C, H, W)
    return out


# ============================================================================
# Attention Mechanisms
# ============================================================================

class SE(nn.Module):
    """Squeeze-and-Excitation block"""
    def __init__(self, c1, ratio=16):
        super(SE, self).__init__()
        self.avgpool = nn.AdaptiveAvgPool2d(1)
        self.l1 = nn.Linear(c1, c1 // ratio, bias=False)
        self.relu = nn.ReLU(inplace=True)
        self.l2 = nn.Linear(c1 // ratio, c1, bias=False)
        self.sig = nn.Sigmoid()

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avgpool(x).view(b, c)
        y = self.l1(y)
        y = self.relu(y)
        y = self.l2(y)
        y = self.sig(y)
        y = y.view(b, c, 1, 1)
        return x * y.expand_as(x)


class SELayer(nn.Module):
    """SE Layer for feature recalibration (PP-LCNet variant)"""
    def __init__(self, channel, reduction=4):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Hardsigmoid(inplace=True)
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)


class ECA(nn.Module):
    """Efficient Channel Attention"""
    def __init__(self, k_size=3):
        super(ECA, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        y = self.avg_pool(x)
        y = self.conv(y.squeeze(-1).transpose(-1, -2)).transpose(-1, -2).unsqueeze(-1)
        y = self.sigmoid(y)
        return x * y.expand_as(x)


class CoordAtt(nn.Module):
    """Coordinate Attention mechanism"""
    def __init__(self, inp, oup, reduction=32):
        super(CoordAtt, self).__init__()
        self.pool_h = nn.AdaptiveAvgPool2d((None, 1))
        self.pool_w = nn.AdaptiveAvgPool2d((1, None))
        mip = max(8, inp // reduction)
        self.conv1 = nn.Conv2d(inp, mip, kernel_size=1, stride=1, padding=0)
        self.bn1 = nn.BatchNorm2d(mip)
        self.act = h_swish()
        self.conv_h = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)
        self.conv_w = nn.Conv2d(mip, oup, kernel_size=1, stride=1, padding=0)

    def forward(self, x):
        identity = x
        n, c, h, w = x.size()
        x_h = self.pool_h(x)
        x_w = self.pool_w(x).permute(0, 1, 3, 2)
        y = torch.cat([x_h, x_w], dim=2)
        y = self.conv1(y)
        y = self.bn1(y)
        y = self.act(y)
        x_h, x_w = torch.split(y, [h, w], dim=2)
        x_w = x_w.permute(0, 1, 3, 2)
        a_h = self.conv_h(x_h).sigmoid()
        a_w = self.conv_w(x_w).sigmoid()
        out = identity * a_w * a_h
        return out


class GAMAttention(nn.Module):
    """Global Attention Mechanism"""
    def __init__(self, c1, c2, group=True, rate=4):
        super(GAMAttention, self).__init__()

        self.channel_attention = nn.Sequential(
            nn.Linear(c1, int(c1 / rate)),
            nn.ReLU(inplace=True),
            nn.Linear(int(c1 / rate), c1)
        )
        self.spatial_attention = nn.Sequential(
            nn.Conv2d(c1, c1 // rate, kernel_size=7, padding=3, groups=rate) if group else nn.Conv2d(c1, int(c1 / rate), kernel_size=7, padding=3),
            nn.BatchNorm2d(int(c1 / rate)),
            nn.ReLU(inplace=True),
            nn.Conv2d(c1 // rate, c2, kernel_size=7, padding=3, groups=rate) if group else nn.Conv2d(int(c1 / rate), c2, kernel_size=7, padding=3),
            nn.BatchNorm2d(c2)
        )

    def forward(self, x):
        b, c, h, w = x.shape
        x_permute = x.permute(0, 2, 3, 1).view(b, -1, c)
        x_att_permute = self.channel_attention(x_permute).view(b, h, w, c)
        x_channel_att = x_att_permute.permute(0, 3, 1, 2)
        x = x * x_channel_att

        x_spatial_att = self.spatial_attention(x).sigmoid()
        x_spatial_att = channel_shuffle(x_spatial_att, 4)
        out = x * x_spatial_att
        return out


class SimAM(torch.nn.Module):
    """Simple Attention Module"""
    def __init__(self, e_lambda=1e-4):
        super(SimAM, self).__init__()
        self.activaton = nn.Sigmoid()
        self.e_lambda = e_lambda

    def forward(self, x):
        b, c, h, w = x.size()
        n = w * h - 1
        x_minus_mu_square = (x - x.mean(dim=[2, 3], keepdim=True)).pow(2)
        y = x_minus_mu_square / (4 * (x_minus_mu_square.sum(dim=[2, 3], keepdim=True) / n + self.e_lambda)) + 0.5
        return x * self.activaton(y)


# ============================================================================
# Multi-dimensional Collaborative Attention (MCA)
# ============================================================================

class StdPool(nn.Module):
    """Standard deviation pooling"""
    def __init__(self):
        super(StdPool, self).__init__()

    def forward(self, x):
        b, c, _, _ = x.size()
        std = x.view(b, c, -1).std(dim=2, keepdim=True)
        std = std.reshape(b, c, 1, 1)
        return std


class MCAGate(nn.Module):
    """Multi-dimensional Collaborative Attention Gate"""
    def __init__(self, k_size, pool_types=['avg', 'std']):
        super(MCAGate, self).__init__()

        self.pools = nn.ModuleList([])
        for pool_type in pool_types:
            if pool_type == 'avg':
                self.pools.append(nn.AdaptiveAvgPool2d(1))
            elif pool_type == 'max':
                self.pools.append(nn.AdaptiveMaxPool2d(1))
            elif pool_type == 'std':
                self.pools.append(StdPool())
            else:
                raise NotImplementedError

        self.conv = nn.Conv2d(1, 1, kernel_size=(1, k_size), stride=1, padding=(0, (k_size - 1) // 2), bias=False)
        self.sigmoid = nn.Sigmoid()
        self.weight = nn.Parameter(torch.rand(2))

    def forward(self, x):
        feats = [pool(x) for pool in self.pools]

        if len(feats) == 1:
            out = feats[0]
        elif len(feats) == 2:
            weight = torch.sigmoid(self.weight)
            out = 1 / 2 * (feats[0] + feats[1]) + weight[0] * feats[0] + weight[1] * feats[1]
        else:
            assert False, "Feature Extraction Exception!"

        out = out.permute(0, 3, 2, 1).contiguous()
        out = self.conv(out)
        out = out.permute(0, 3, 2, 1).contiguous()

        out = self.sigmoid(out)
        out = out.expand_as(x)

        return x * out


class MCALayer(nn.Module):
    """Multi-dimensional Collaborative Attention Layer"""
    def __init__(self, inp, no_spatial=True):
        super(MCALayer, self).__init__()

        lambd = 1.5
        gamma = 1
        temp = round(abs((math.log2(inp) - gamma) / lambd))
        kernel = temp if temp % 2 else temp - 1

        self.h_cw = MCAGate(3)
        self.w_hc = MCAGate(3)
        self.no_spatial = no_spatial
        if not no_spatial:
            self.c_hw = MCAGate(kernel)

    def forward(self, x):
        x_h = x.permute(0, 2, 1, 3).contiguous()
        x_h = self.h_cw(x_h)
        x_h = x_h.permute(0, 2, 1, 3).contiguous()

        x_w = x.permute(0, 3, 2, 1).contiguous()
        x_w = self.w_hc(x_w)
        x_w = x_w.permute(0, 3, 2, 1).contiguous()

        if not self.no_spatial:
            x_c = self.c_hw(x)
            x_out = 1 / 3 * (x_c + x_h + x_w)
        else:
            x_out = 1 / 2 * (x_h + x_w)

        return x_out


# ============================================================================
# LMWP-YOLO Core Modules
# ============================================================================

class LightweightMSFFM(nn.Module):
    """Lightweight Multi-Scale Feature Fusion Module"""
    def __init__(self, inp):
        super(LightweightMSFFM, self).__init__()
        self.conv1 = nn.Conv2d(inp, inp // 8, kernel_size=1)
        self.conv3 = nn.Conv2d(inp, inp // 8, kernel_size=3, padding=1, groups=inp // 8)
        self.conv5 = nn.Conv2d(inp, inp // 8, kernel_size=5, padding=2, groups=inp // 8)
        self.conv7 = nn.Conv2d(inp, inp // 8, kernel_size=7, padding=3, groups=inp // 8)
        self.fusion = nn.Conv2d(inp // 2, inp, kernel_size=1)
        self.relu = nn.ReLU(inplace=True)
        self.se = SELayer(inp)

    def forward(self, x):
        x1 = self.conv1(x)
        x3 = self.conv3(x)
        x5 = self.conv5(x)
        x7 = self.conv7(x)
        out = torch.cat([x1, x3, x5, x7], dim=1)
        out = self.relu(self.fusion(out))
        out = self.se(out)
        return out + x


class MiniResidualBlock(nn.Module):
    """Mini Residual Block for feature refinement"""
    def __init__(self, channels):
        super(MiniResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out += residual
        out = self.relu(out)
        return out


class MAFR(nn.Module):
    """
    Multi-scale Adaptive Feature Refinement Module

    Core component of LMWP-YOLO that combines:
    - Multi-dimensional Collaborative Attention (MCA)
    - Lightweight Multi-Scale Feature Fusion (LMSFFM)
    - Residual refinement

    Designed for enhanced small drone detection in challenging conditions.
    """
    def __init__(self, inp, no_spatial=True):
        super(MAFR, self).__init__()
        self.mca = MCALayer(inp, no_spatial)
        self.lmsffm = LightweightMSFFM(inp)
        self.mini_res = MiniResidualBlock(inp)

    def forward(self, x):
        x_mca = self.mca(x)
        x_lmsffm = self.lmsffm(x_mca)
        x_out = self.mini_res(x_lmsffm)
        return x_out


# ============================================================================
# PP-LCNet Backbone Components
# ============================================================================

class DepthSepConv(nn.Module):
    """Depthwise Separable Convolution (DW + PW)"""
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, use_se=False):
        super().__init__()
        padding = (kernel_size - 1) // 2

        # Depthwise convolution
        self.dw_conv = nn.Conv2d(
            in_channels, in_channels,
            kernel_size=kernel_size, stride=stride, padding=padding,
            groups=in_channels, bias=False
        )
        self.dw_bn = nn.BatchNorm2d(in_channels)

        # Pointwise convolution
        self.pw_conv = nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False)
        self.pw_bn = nn.BatchNorm2d(out_channels)

        self.act = HardSwish(inplace=True)

        # Optional SE attention
        self.use_se = use_se
        if use_se:
            self.se = SELayer(out_channels)

    def forward(self, x):
        # Depthwise
        x = self.dw_conv(x)
        x = self.dw_bn(x)
        x = self.act(x)

        # Pointwise
        x = self.pw_conv(x)
        x = self.pw_bn(x)

        # SE attention
        if self.use_se:
            x = self.se(x)

        x = self.act(x)
        return x


class PPLCNetStem(nn.Module):
    """
    PP-LCNet Stem (initial convolution)

    Input: 3 channels (RGB)
    Output: 12 channels (16 * 0.75 scale)
    Stride: 2 (1/2 resolution)
    """
    def __init__(self, c1=3, c2=12):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(c1, c2, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(c2),
            HardSwish(inplace=True)
        )

    def forward(self, x):
        return self.stem(x)


class PPLCNetStage(nn.Module):
    """
    PP-LCNet Stage (stack of DepthSepConv blocks)

    Args:
        c1: Input channels
        c2: Output channels
        num_blocks: Number of DepthSepConv blocks in this stage
        stride: Stride for first block (subsequent blocks use stride=1)
        kernel_size: Kernel size for depthwise conv
        use_se: Whether to use SE attention
    """
    def __init__(self, c1, c2, num_blocks=2, stride=2, kernel_size=3, use_se=False):
        super().__init__()

        blocks = []
        for i in range(num_blocks):
            block_stride = stride if i == 0 else 1
            block_in = c1 if i == 0 else c2

            blocks.append(
                DepthSepConv(
                    block_in, c2,
                    kernel_size=kernel_size,
                    stride=block_stride,
                    use_se=use_se
                )
            )

        self.stage = nn.Sequential(*blocks)

    def forward(self, x):
        return self.stage(x)


# Predefined stage configurations for PP-LCNet 0.75x

class PPLCNetStage1(PPLCNetStage):
    """PP-LCNet Stage 1 → P2 (1/4 resolution), 12→48 channels"""
    def __init__(self, c1=12, c2=48):
        super().__init__(c1=c1, c2=c2, num_blocks=2, stride=2, kernel_size=3, use_se=False)


class PPLCNetStage2(PPLCNetStage):
    """PP-LCNet Stage 2 → P3 (1/8 resolution), 48→96 channels"""
    def __init__(self, c1=48, c2=96):
        super().__init__(c1=c1, c2=c2, num_blocks=2, stride=2, kernel_size=3, use_se=False)


class PPLCNetStage3(PPLCNetStage):
    """PP-LCNet Stage 3 → P4 (1/16 resolution), 96→192 channels"""
    def __init__(self, c1=96, c2=192):
        super().__init__(c1=c1, c2=c2, num_blocks=2, stride=2, kernel_size=5, use_se=False)


class PPLCNetStage4(PPLCNetStage):
    """PP-LCNet Stage 4 → P5 (1/32 resolution), 192→384 channels"""
    def __init__(self, c1=192, c2=384):
        super().__init__(c1=c1, c2=c2, num_blocks=2, stride=2, kernel_size=5, use_se=False)
