# External Technical Evidence

This file records external technical discussion and reproduction evidence for this repository. It is intentionally narrower than a testimonial or endorsement record.

## IETF OAuth Working Group discussion — September 13–14, 2026

### Original problem statement

Valentyn Rukhaylo opened an OAuth Working Group discussion on **execution-time state binding for OAuth-authorized agent actions** and signed the message as **Valentyn Rukhaylo / Altru.dev**.

Archive:
- https://www.mail-archive.com/oauth%40ietf.org/msg26689.html

The discussion explicitly asked whether existing OAuth/HTTP mechanisms already covered the problem and did not assume a standards gap.

### External challenge and narrowing

Kieran Sweeney pointed to RFC 9110 conditional requests and RFC 9396 Rich Authorization Requests as existing mechanisms relevant to the simpler case, and asked for a concrete counterexample.

Archive:
- https://mailarchive.ietf.org/arch/msg/oauth/18WRRSjwZilvmtNLh4fKtZMRKMg/

This narrowed the experiment toward independently changing prerequisite state rather than target-resource state alone.

### Independent reproduction of the eight-scenario probe

Iman Schrock reported that he:
- checked the supplied SHA-256;
- reran the probe; and
- obtained all eight scenario outputs matching the supplied `results.json`.

He also identified two weaknesses in that reviewed probe:
- T4 calculated a predicate but did not yet exercise the actual guarded execution path; and
- T7b changed the prerequisite version but did not yet make the approved-to-suspended state change explicit.

Archive:
- https://mailarchive.ietf.org/arch/msg/oauth/4ddQ_j-pND-0VkY8fY0qtl4nyQo/

### Post-review strengthening

After that review, Valentyn Rukhaylo strengthened T4 and T7b and published the revised probe in pinned commit:

- https://github.com/altrudev/authorization-transition-closure/commit/502d27e5fea506fab708bcdec48f14b60ab3f2eb

The updated probe SHA-256 reported in the mailing-list archive was:

`749461e8cff8bf66aabd393957be79b76e292d0f3e0440f1c322f168b3fc21f0`

Archive:
- https://www.mail-archive.com/oauth%40ietf.org/msg26709.html

### Important evidence boundary

The independent reproduction described above applies to the **reviewed eight-scenario probe before the T4/T7b strengthening**. The mailing-list record cited here does **not** establish that Iman Schrock independently reran the later pinned commit after those changes.

The pinned revision records the response to the review and makes the strengthened artifact public and reproducible. It should not be described as independently reproduced unless a separate record establishes that fact.

The probe is a deterministic in-memory model. It does not by itself test OAuth servers, HTTP servers, WebDAV servers, EMILIA/AEB implementations, or participating providers, and it does not by itself establish a standards gap.

## What this record establishes

This record supports the narrower claims that:
1. the research question was discussed in a public IETF OAuth WG archive;
2. an external participant independently reproduced the reviewed eight-scenario probe and reported matching outputs;
3. that participant challenged specific weaknesses in the probe; and
4. the repository subsequently published a strengthened pinned revision responding to those weaknesses.

It does not establish standards adoption, protocol correctness, production interoperability, certification, or endorsement by the IETF or its participants.
