# Spatial Data Nomenclature #

In the context of spatial data, Attributes is the standard and most widely used term in the industry.

While the "spatial" part refers to the geometry (the coordinates that define the shape of a Brazilian state), the "attribute" part refers to the non-spatial data associated with that shape.

Here is a breakdown of how this is categorized in spatial data jargon:

## Attribute Data ##
This refers to the tabular information attached to a geographic feature. In your example of Brazilian states, the attributes would include:

- ID / Primary Key: Often an IBGE code or a UUID.
- Name: e.g., "São Paulo" or "Amazonas".
- ISO Code: e.g., "SP" or "AM".

Statistical Data:

- Population
- GDP, or
- area.

## Spatial Data (Geometry) ##
This is the mathematical representation of the feature. It is usually stored in a specific column (often named geom, geometry, or shape) and contains:

Feature Type:
- Point
- Line
- or Polygon (in this case, MultiPolygon).

Coordinates:
- The vertices that define the borders.

## Related Terminology ##
While *attributes* is the go-to term, you might encounter these variations depending on the software or field:

- *Fields/Columns:*
Common in GIS software like QGIS or ArcGIS, referring to the "Attribute Table" which functions much like a standard database table or spreadsheet.

- *Properties:*
Frequently used in GeoJSON format. A GeoJSON object is typically split into "geometry" and "properties".

- *Feature Attributes:*
A more formal way to describe the characteristics of a "feature" (the combination of geometry + data).

- *Variables:*
Often used in spatial statistics or data science (e.g., when using Python libraries like geopandas).


### Summary ###
If you are writing documentation or code for a spatial project, sticking with Attributes is the most professional and technically precise choice. It clearly distinguishes the "what" (the data) from the "where" (the geometry).


## Attributes Names ##

|Attribute| DB Col Name | UI |
| --- | --- | --- |
|``ID``| field_id | id
|``name``| field_name | nome|
|``alt_name``| field_flt_name | _see the table below_|

|Context|Suggested pt-BR Label|
|---|---|
|Standard/Technical|Nome alternativo|
|Hierarchical|Nome secundário|
|User-Friendly|Conhecido como|
|hort/Label|Alcunha or Apelido (Only if informal)|


_Gemini_