# Tonalogy API

Backend Service for Tonal Analysis and Visualization

## Project Context

This repository contains the primary backend service for the Tonalogy project. It implements the server-side logic, including the analysis engine and the visual rendering component. For a complete conceptual overview of the Tonalogy system, its theoretical foundations in modal logic, and its academic goals, please refer to the [main project documentation](https://github.com/joabemorais/tonalogy).
This service is a direct implementation of the computational model proposed in the undergraduate thesis:

> “Uma Implementação Computacional para Análise de Tonalidade em Progressões Harmônicas via Semântica de Mundos Possíveis”

## Architectural Role

The Tonalogy API is structured internally into distinct components with clear responsibilities:

- **Tonalogy Core**: The inference engine responsible for the formal analysis of harmonic progressions based on Kripke semantics. It receives chord sequences and outputs structured semantic data.
- **Tonalogy Visualizer**: The rendering module that translates the structured data from the Core into visual diagrams, manipulating SVG templates to generate PNG images that represent the tonal analysis.
- **API Layer**: The web layer, built with FastAPI, that exposes the functionalities of the Core and Visualizer through RESTful endpoints, serving as the gateway for all clients.

## Technology Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Data Modeling**: Pydantic
- **Graph Generation Engine**: Graphviz
- **Core Dependencies**: `cairosvg`, `python-graphviz`
