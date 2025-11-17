# SunWalk -- Real-Time Urban Sun & Shade Mapping for Berlin

SunWalk is an experimental GIS application that maps real-time sun and
shade conditions in urban environments.\
The project explores how to combine building geometry, solar position
algorithms, and walk-path optimization to help users choose the sunniest
or shadiest routes---starting with Berlin.

This repository presents the early architecture, development roadmap,
and initial geospatial experiments toward a future MVP.

------------------------------------------------------------------------

## Project Purpose

Urban microclimates strongly influence comfort, especially in cities
like Berlin where winter sun is valuable.\
SunWalk aims to:

-   calculate dynamic shadows based on building heights and solar
    geometry\
-   visualize real-time sun conditions on a map\
-   enable "sun-optimized" or "shade-optimized" walking routes\
-   support urban analytics, public health, and climate-adaptive
    planning

------------------------------------------------------------------------

## Project Architecture (Preview)

The current architecture outlines:

-   Berlin AOI ingestion via OSM\
-   building geometry extraction and cleaning\
-   solar position modeling\
-   ray-tracing--based shade estimation\
-   map rendering pipeline for a future web app

![SunWalk Architecture](docs/architecture.png)

------------------------------------------------------------------------

## Development Roadmap

This roadmap highlights the planned path from research to MVP.

![SunWalk Roadmap](docs/roadmap.png)

------------------------------------------------------------------------

## Experiments Included in This Repo

Early-stage development includes:

-   OSMnx (v2.11+) data extraction\
-   building footprint and height processing\
-   sunlight/shadow test plots\
-   first AOI selection for Berlin (Mitte)\
-   notebook-based demonstrators (Colab-ready)

Reproducible experiments can be found under:

    /notebooks

------------------------------------------------------------------------

## Repository Structure

    sunwalk/
    ├── README.md
    ├── docs/
    │   ├── architecture.png
    │   ├── roadmap.png
    │   └── concept.md
    ├── notebooks/
    │   └── berlin_sunwalk_osm_aoi_experiments.ipynb
    ├── src/
    │   ├── data/
    │   ├── preprocessing/
    │   ├── gis/
    │   └── sunlight/
    └── examples/
        └── first_plot_banner.png

------------------------------------------------------------------------

## Next Steps

-   implement complete shade-projection engine\
-   integrate atmospheric parameters\
-   add fallback estimation for missing building heights\
-   prototype interactive web map (MapLibre, deck.gl, or WebGL)\
-   develop path-optimization module for sun or shade routes

------------------------------------------------------------------------

## License

MIT License (recommended for open research projects).\
Add your license file to `LICENSE`.

------------------------------------------------------------------------

## Author

**Giovani Bonadiman Goltara**\
Urban Research · UX Design · GIS · Data Analysis
