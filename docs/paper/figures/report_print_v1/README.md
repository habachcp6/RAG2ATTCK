# Report-Print Figure Variants (`report_print_v1`)

## 1. Publication Role Mapping

| Target Role | Variant Asset | Format Availability | Purpose |
|---|---|---|---|
| **Final Report Figure 1** | `fig1_system_architecture_report_v1` | SVG, PNG, PDF | 468pt single-column Word report architecture layout with readable fonts (>= 8.5pt) |
| **Final Report Figure 5** | `fig5_conditional_accuracy_report_v1` | SVG, PNG, PDF | 468pt single-column Word report conditional accuracy layout with exact subgroup counts (N=321, N=397) and 2-line observational caveat |

## 2. Legacy Defect Record & Governance Boundaries

> [!IMPORTANT]
> **Legacy Figure 1 Defect Disclosure:**
> The legacy draft figure (`fig1_system_architecture`) contained an inherited financial label defect: `"$0.0526 hold/request"`. This erroneously conflated the global whole-study prior-pilot provisional hold (`$0.05264010`) with per-request reservations.
> 
> - **Legacy Authority Status:** Legacy Figure 1 was an exploratory draft and **was never selected as the final publication authority**.
> - **Corrected Approved Authority:** The approved report-print variant (`fig1_system_architecture_report_v1`) strictly uses the verified whole-study financial guard label:
>   - Header: `USD19.99 study cap; reserve before dispatch`
>   - Detail: `Atomic dual-lock ledger reservation`
> - **D1 Prompt Policy Correction:** Decision D1 is explicitly stated as:
>   - `No in-flight prompt mutations; retries recorded in attempt journal`
>   This truthfully accounts for the canonical attempt journal (6,401 total attempts for 6,400 completed records, reflecting exactly 1 transport retry under policy).

## 3. Physical Scale and Layout Specification

- **Target Placement Width:** 468pt (standard single-column width for 1-inch margins on US Letter / A4).
- **Minimum Font Size Threshold:** >= 8.5pt across all labels, captions, and caveats.
- **Figure 5 Title Scaling:** Rendered with CSS `.title` at 12.5px (user units), which scales to exactly 12.5pt physical font size when placed at 468pt column width.
- **Raster PNG Placement:** 468x550 (Fig 1) and 468x440 (Fig 5) achieve >= 8.5pt font size when placed at 468pt width in Microsoft Word / document consumers.
- **Vector PDF Placement:** Native PDF width is 351.12pt due to the standard 0.75 CSS px-to-pt viewport conversion. Document consumers must place/scale the PDF to 468pt column width to achieve the certified >= 8.5pt physical print scale. Standalone unscaled 100% PDF viewing does not claim 8.5pt.
