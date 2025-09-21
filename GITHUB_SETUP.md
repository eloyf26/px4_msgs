# GitHub Repository Setup

Your Halcon1 System repository is ready to push to GitHub!

## Manual Setup Steps

### 1. Create Repository on GitHub

Go to https://github.com/new and create a new repository:
- **Name**: `halcon1-system`
- **Description**: Complete autonomous drone interception system with PX4 SITL and ROS2 pipeline
- **Visibility**: Public (or Private if preferred)
- **Initialize**: DO NOT add README, .gitignore, or license (already in local repo)

### 2. Add Remote and Push

After creating the empty repository, run these commands:

```bash
cd ~/drone_ws

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/halcon1-system.git

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### 3. Alternative: Using GitHub CLI

If you want to use GitHub CLI in the future:

```bash
# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update
sudo apt install gh

# Authenticate
gh auth login

# Create and push repository
gh repo create "halcon1-system" --public --source . --push
```

## Repository Contents

Your repository includes:
- ✅ Complete Halcon1 ROS2 packages
- ✅ PX4 and MicroXRCE as git submodules
- ✅ One-click setup script
- ✅ Launch scripts for all components
- ✅ Comprehensive documentation
- ✅ .gitignore excluding build artifacts

## After Pushing

Update the README.md to replace:
```
git clone --recursive https://github.com/yourusername/halcon1-system.git
```

With your actual GitHub username.

## Cloning on Another Machine

```bash
git clone --recursive https://github.com/YOUR_USERNAME/halcon1-system.git
cd halcon1-system
./setup.sh
```

The `--recursive` flag ensures submodules are cloned too.