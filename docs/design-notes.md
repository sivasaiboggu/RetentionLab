# Dashboard design decisions

The page is a research workbench, not a marketing template. The numbers,
uncertainty and next analyst action should be readable before decoration.

## Reference review, 2026-10-23

| Reference | Direction taken | What was not reused |
|---|---|---|
| [Landdding](https://landdding.com), [Godly](https://godly.website), [Recent](https://recent.design) | Distinct type hierarchy, whitespace and deliberate sections | No template markup, screenshots or copied layout assets |
| [Font In Logo](https://fontinlogo.com) | Contrast display, interface and metadata type roles | No logo or trademark copied |
| [Footer Design](https://footer.design) | Quiet closing rule and compact metadata | No decorative footer that distracts from analysis |
| [Modulify](https://modulify.ai) | Consistent reusable surface patterns | No account, generated site or paid builder required |
| [Motion](https://motionin.design) | One short entrance instead of constant movement | No premium interactive sections, scroll hijacking or autoplay |
| [Wonderlist](https://wonderlist.design) | Consistent spacing and reusable surface rules | Paid Figma packs were not purchased or copied |
| [Iconly](https://iconly.design) | Small, coherent mark rather than an icon collage | No app icons/trademarks copied; letter marks are original CSS |
| [On Design](https://on.design) | Cohesion across related product screens | No external product UI or assets copied |
| [60fps](https://60fps.design) | Hover/focus feedback and visible control state | No inaccessible motion-heavy interactions |
| [Backgrounds Supply](https://backgrounds.supply) | Restraint: flat analytical canvas | No paid backgrounds downloaded or reused |

Instrument Serif, DM Sans and DM Mono are embedded locally under their OFL
licenses in `assets/fonts/`. No font CDN or tracker is needed. Graphite/sage/ivory
remain the base palette; muted text and rules use alpha, not new accent colors.

Four metrics become a two-by-two mobile grid. Four charts keep short titles.
The table remains horizontally scrollable within its own frame rather than
breaking document width. Numbered sections, thin rules and chart panels create
rhythm without adding a sidebar or extra pages. Focus rings stay visible, and
reduced-motion disables entrance animation. Stock Streamlit form/table behavior
is retained where it supports reliable keyboard use; custom CSS is not a new
frontend framework. CSS selectors are tied to the pinned Streamlit version and
must be rechecked during upgrades.

Screenshots were inspected at 1280, 390 and 320 CSS-pixel viewport widths. No
layout claim substitutes for data or human-validation evidence.

## Library revision and Power BI kit

The current palette is graphite #151D21, sage #A8C4A2 and ivory #F3F0E7,
with a tonal #202B30 surface. It replaces the earlier navy/orange theme.
`streamlit-extras.metric_cards` styles the KPI cards. `streamlit-option-menu`
controls the queue population or sorting; it is not decorative navigation.
Three Plotly charts and one Altair chart keep the same frozen evidence.
The Power BI JSON theme uses matching colors, but its build kit has not been
rendered in Desktop and is not a completed PBIX file.
