Cattle-Vision Annotation Guidelines
-----------------------------------

Class:
    cow

Include:
    - all identifiable bovines
    - partially occluded bovines
    - bovines seen from any direction
    - small but identifiable bovines

Exclude:
    - stones
    - vegetation
    - tree trunks
    - shadows
    - ambiguous objects that cannot confidently
      be identified as cattle

Occlusion:
    - annotate each visible bovine individually
    - do not merge overlapping animals

Bounding box:
    - tightly enclose the visible animal
    - do not include unnecessary background

NADIR / OBLIQUE:
    - same class: cow
    - do not encode camera orientation in the label