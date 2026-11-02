## Title

[OC] How much of the world Europe had written about or mapped, 1400 BC to 1960: 20% of the land in 1492, 44% in 1800, and the parts other traditions had recorded first

## Body

You may know the animation of world exploration from Europe's point of view. I rebuilt it as data, and tried to make it honest. I compiled 681 journeys with dated routes, from Austronesian voyages out of Taiwan to 1950s crossings of Antarctica, and lit up an equal-area grid wherever a route passed close enough to describe a place. Europe starts from the Bronze Age Aegean rather than from nothing, so Ptolemy's world is already lit in AD 150 (15% of the land). Because much of the world was mapped by surveyors and settlers rather than explorers, Europe also has a coarse layer of 52 surveyed or settled regions (US township survey, Canadian prairies, Russia, India, Australia...), which you can switch off: journeys alone reach 64% of the land by 1960, journeys plus surveys 80%. Then very little happens for a thousand years. Half of the Earth's surface was lit for Europe by 1809, half of its land only by 1841, and the 1800s added the most. The interactive version lets you switch the point of view to the Islamic world, China or Polynesia: China had recorded 18.8 million km2 before Europe did, and Polynesians settled Hawaii around 1219, centuries before Cook. Caveats: every dark place was known to the people living there; the gazetteer leans on English-language sources; the survey layer's dates are mine and coarse; the reveal distances are a choice (1960 land share 58% to 86% across variants). Interactive map: https://maps.tristanhotham.com/known-world/

## Source comment

Sources: a gazetteer of 681 journey routes and 52 survey and settlement regions compiled for this study, mostly from English Wikipedia (CC BY-SA) and the accounts it cites, with a source status for every journey; Natural Earth (land, ice shelves, countries); H3 equal-area hexagonal grid.

Tools: Python (numpy, scipy, scikit-learn, shapely, h3, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/known-world/
Paper: https://doi.org/10.5281/zenodo.23897793
Blog post: https://blog.tristanhotham.com/2026/10/31/known-world/
