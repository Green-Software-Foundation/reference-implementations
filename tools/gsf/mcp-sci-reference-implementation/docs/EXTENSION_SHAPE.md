# Extension shape (one page)

Identifier: `foundation.greensoftware/sustainability`
Status: experimental, for discussion. Not a specification.

## 1. `server/discover` – settings object

| Field | Meaning |
|---|---|
| `version` | Version of this extension shape. |
| `methodology` | Which GSF standard the figures follow. |
| `publisher` | Who owns the figures (may differ from the server, e.g. a gateway). |

## 2. `tools/list` – disclosure, per tool, in `_meta`

| Field | Meaning |
|---|---|
| `methodology.id / base / uri` | `SCI-for-AI`, built on ISO SCI. |
| `functionalUnit.name / description` | The unit of work the score is per. |
| `boundary.persona` | `provider` or `consumer` (SCI for AI). |
| `boundary.phase` | `inference`, `training`, `fine-tuning`, ... |
| `boundary.description` | Plain text, authoritative. |
| `boundary.includes / excludes` | Tags so software can compare boundaries. |
| `typical.sci / energy / basis / note` | A representative figure so a client can reason before calling. |

Static. The server sets a `tools/list` cache hint so clients need not refetch.

## 3. `tools/call` result – attribution, in `_meta`

Only sent when the request declared the extension in client capabilities.

| Field | Meaning |
|---|---|
| `functionalUnit.name / quantity` | Units of work this call completed. |
| `boundary.persona / phase` | Repeated for convenience. |
| `energy.value / unit / basis` | E. `basis` is `measured` or `estimated`. |
| `carbonIntensity.value / unit / region / basis` | I. Location-based. |
| `emissions.operational` | E × I |
| `emissions.embodied` | M |
| `emissions.total` | E × I + M |
| `emissions.embodiedBasis` | `provider-reported` or the estimation rule used. |
| `sci.value / unit` | (E × I + M) / R |
| `details` | Model, tokens, outcome (`completed` / `failed`), energy source. |

## 4. Rules this prototype follows

- A tool with no disclosure simply has no extension key. Nothing is invented.
- A plain client (no extension declared) receives unchanged results.
- Business content and sustainability data never mix; the data lives in `_meta`.
- Every figure says whether it was measured or estimated.

## 5. Open questions for the working group

- Required vs optional fields; a fixed unit list; a fixed boundary vocabulary.
- Assurance level and verifier identity, to guard against greenwashing.
- Signed, fetchable disclosure documents (e.g. `/.well-known/...`).
- Behaviour with the Tasks extension and multi-round-trip requests.
- Water and energy-efficiency metrics (SEE) alongside carbon.
- Aggregation across an agent workflow without double counting.
