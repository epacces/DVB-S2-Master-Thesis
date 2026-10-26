# <a id="chapter-8"></a>8 Conclusions

In this thesis we have dealt with a digital communications TX section which can provide a reliable information transmission via satellite while complying with the challenging requirements on performance imposed by the DVB-S2 standard.

My main contributions to the overall project of the DVB-S2 TX section developed by TAS-I have been focused specifically on

- study of the theory underlying the BCH code: Galois fields and cyclic codes theory in order to have the theoretical basis to understand the DVB-S2 code structure and analyze related algorithms;

- theoretical analysis of DVB-S2 BCH code structure from which we have reached the conclusion that the DVB-S2 outer code (BCH) must be *primitive* and *shortened*;

- study of the BCH encoding procedures and algorithms and its related (serial) architectures;

- modelling and design of a parallel BCH encoder with a high degree of parallelism in order to best match the TX Section (developed by TAS) speed requirements;

- development of a Berlekamp-Massey software decoder in order to give a proof of the error correction capacity of the code (encoder); for this purpose we have defined specific routines aimed to compute arithmetic tables useful in decoding and error detection computations;

- development of a software package (C/C++) in order to verify the functioning of the architectures envisaged and give support to VLSI designers in the validation of the corresponding VHDL model;

Concerning the DVB-S2 architecture and overall TX section and thanks to the contribution of the TAS-I Algorithm & Architectures team, this thesis has dealt with:

- identification of the strategic importance of satellite communications in some application scenarios such as Multimedia, Earth observation, radio-localization and navigation, *etc.*;

- review of novel techniques aimed at obtaining top performance by handling modulation and coding schemes jointly;

- assessment of the features of ACM techniques, which allow better utilization of resources onboard while ensuring a high QoS (Quality of Service);

- design of the DVB-S2 Modem architecture and blocks focusing on concatenated coding (BCH-LDPC) and modulation schemes;

- qualitative description of LDPC encoding/decoding algorithms, and on the latter we have highlighted the importance of the BCH code to counteract error floors affecting LDPC *iterative decodings*;

- BCH encoding procedures and algorithms and its related (serial) architectures;

- modelling and design of a parallel encoder with a high degree of parallelism in order to best match the TX Section (developed by TAS-I) speed requirements;

- selection between two possible (and functionally equivalent) BCH parallel architectures in order to work in ACM;

- development of a Berlekamp-Massey software decoder in order to give a proof of the error correction capacity of the code (encoder); for this purpose we have defined specific routines aimed to compute arithmetic tables useful in decoding and error detection computations;

- development of a software package (C/C++) in order to verify the functioning of the architectures envisaged and give support to VLSI designers in the validation of the corresponding VHDL model;

- participation in a preliminary laboratory test and validation of the TAS-I developed DVB-S2 TX section.

---

[← Preliminary Laboratory Test of DVB-S2 TX Section](08-preliminary-laboratory-test-of-dvb-s2-tx-section.md) · [Contents](README.md) · [Galois (or Finite) Fields →](10-galois-or-finite-fields.md)
