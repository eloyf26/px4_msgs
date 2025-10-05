
## Technology Readiness Levels (TRLs)

TLRs asses the maturity of a particular technology. In defense tech development, we have these:

- **TRL 1**: Observation and reporting of basic principles.
- **TRL 2**: Formulation of the technology and application.
- **TRL 3**: Analytical and experimental critical function and/or characteristic proof of concept.
- **TRL 4**: Validation of component and/or arrangement of components in a laboratory environment.

TRL 4 is the minimum required for a demonstrator, and it is our goal for November 7th 2025.

- **TRL 5**: Validation of component and/or arrangement of components in a relevant environment.
- **TRL 6**: System or subsystem model or prototype demonstration in a relevant environment.
- **TRL 7**: System or prototype demonstration in a real environment.
- **TRL 8**: Complete system certified through tests and demonstrations.
- **TRL 9**: System successfully tested in a real environment.

### STANAG 4817

STANAG 4817 is a NATO standard for the interoperability of unmanned aerial vehicles (UAVs) and their control systems.
It defines a set of protocols and data formats for communication between UAVs and ground control stations (GCS).

Through this protocol sensor data can be combined and shared to create a precise and complete image of the airspace around
the drone.

### NAIAD

NAIAD is Navantia's (Spanish marine defense company) system of command and control for the tactical integration of unmanned 
vehicles. It abstracts the CMS and provides capabilities for planification, coordination, and monitorization.

NAIAD follows STANAG 4817 principles, including **MDCS** (Monitorization + Command + Control unified in a single station).

NAIAD is based on a service-oriented architecture and standards such as OARIS, ALMAS, and OMG DDS, which form the core for 
internal communications. In adopting standards to integrate UxV across all its domains, it incorporates the CATL 
(Collaborative Autonomy Tasking Layer) specification and I2I (Interoperability to Interchangeability), which are at the c
ore of the future STANAG 4817.

| Term                                             | High-level Description                                                                                                                                                                                   | Further Reading / Source                                            |
| ------------------------------------------------ |----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| **OARIS**                                        | An interface that defines how radar (or other sensor systems) expose data and control interfaces inside a modular combat mission system. Vendor modules can plug into it's common architechture.         | OMG “OARIS – Open Architecture Radar Interface Standard” ([OMG][1]) |
| **ALMAS**                                        | A standard alert data model with delivery and lifetime alert definitions. It provides common semantics for warnings and priorities, and a standard way to represent mission / health / constrain alerts. | OMG “About the Alert Management Service Specification” ([OMG][2])   |
| **OMG DDS**                                      | A data-centric, high-performance publish/subscribe middleware standard for real-time distributed systems                                                                                                 | DDS Foundation: “DDS in Other Standards” ([dds-foundation.org][3])  |
| **CATL (Collaborative Autonomy Tasking Layer)**  | A message protocol / format and tasking layer to enable interoperability accross heterogeneous autonomous platforms.                                                                                     | “Experimental Demonstrations of CATL” ([catl paper][4])             |
| **I2I (Interoperability to Interchangeability)** | A NATO concept/standardization effort to not only interoperate but enable substitution and plug-and-play of UxV systems across nations                                                                   | QinetiQ / NATO “I2I” description (section 6) ([qinetiq.com][5])     |

[1]: https://www.omg.org/spec/OARIS/3.0/Beta1/About-OARIS "OARIS™ — Open Architecture Radar Interface Standard"
[2]: https://www.omg.org/spec/ALMAS "About the Alert Management Service Specification Version 1.4 beta"
[3]: https://www.dds-foundation.org/dds-in-other-standards/ "DDS in Other Standards"
[4]: https://ieeexplore.ieee.org/document/10244669 "Experimental Demonstrations of CATL"
[5]: https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.qinetiq.com/-/media/142698ea69d04ff5ad637f8bfdefbac3.ashx&ved=2ahUKEwikirj_84yQAxWK9rsIHRaaF_4QFnoECDEQAQ&usg=AOvVaw27phKLbWVYYcxwls6Jwh7t "Integrating maritime autonomous systems (MAS)"


