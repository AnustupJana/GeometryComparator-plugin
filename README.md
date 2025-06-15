# Geometry Comparator QGIS Plugin
![Diagram of the System](https://github.com/AnustupJana/GeometryComparator-plugin/blob/main/icon.png?raw=true)

## Overview

The **Geometry Comparator** plugin for QGIS is a tool designed to compare two vector layers (Polygon, Line, or Point) and identify changes between them. Using a unique ID field and geometry-based comparison, the plugin detects **Added**, **Deleted**, and **Modified** features. This is useful for tracking changes in geospatial datasets, such as urban planning, land use monitoring, or infrastructure updates.

## Requirements

- **QGIS Version**: 3.1 or later.
- **Operating System**: Windows, macOS, or Linux (compatible with QGIS installations).
- **Dependencies**: No additional Python libraries required; uses QGIS core and PyQt modules.

## Installation

1. **From QGIS Plugin Repository**:
   - In QGIS, go to `Plugins > Manage and Install Plugins`.
  
     ![Diagram of the System](https://github.com/AnustupJana/PolygonCompare-plugin/blob/main/doc/1st_Plugin.png?raw=true)
   - Search for "Geometry Comparator" in the `All` tab.
   - Click `Install Plugin`.

2. **From ZIP File**:
   - Download the plugin ZIP file from the [GitHub Releases](https://github.com/AnustupJana/GeometryComparator-plugin.git) page.
   - In QGIS, go to `Plugins > Manage and Install Plugins > Install from ZIP`.
   - Select the downloaded ZIP file and click `Install Plugin`.

3. **From Source (for developers)**:
   - Clone or download this repository:
     ```bash
     git clone https://github.com/AnustupJana/GeometryComparator-plugin.git
     ```
   - Copy the `Geometry Comparator` folder to your QGIS plugins directory:
     - Windows: `C:\Users\[YourUsername]\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
     - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
     - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

4. **Enable the Plugin**:
   - In the QGIS Plugin Manager, search for **Geometry Comparator**.
   - Check the box to enable the plugin.

5. **Verify Installation**:
   - Look for the **Geometry Comparator** icon in the QGIS toolbar or find it in the **Vector** menu.
   - Open the Processing Toolbox (`Ctrl+Alt+T`) and locate **Geometry Comparator** under **Vector Analysis**.

## Usage

1. **Launch the Plugin**:
   - Click the **Geometry Comparator** toolbar icon or select **Geometry Comparator** from the **Vector** menu.
   - Alternatively, open the Processing Toolbox (`Ctrl+Alt+T`), navigate to **Vector Analysis**, and double-click **Geometry Comparator**.

2. **Configure Parameters**:
   - **Geometry Type**: Select the geometry type of your layers (Polygon, Line, or Point).
   - **Old Layer**: Choose the older vector layer to compare.
   - **New Layer**: Choose the newer vector layer to compare.
   - **Unique ID Field**: Select a field containing unique IDs. This field must exist in both layers.
   - **Output Layers**:
     - **Modified Features**: Specify the destination for modified features (default: temporary layer).
     - **Added Features**: Specify the destination for added features (default: temporary layer).
     - **Deleted Features**: Specify the destination for deleted features (default: temporary layer).

3. **Run the Algorithm**:
   - Click **Run** in the dialog to process the layers.
   - The plugin will validate inputs and compare features based on IDs and geometries.
   - Progress and feedback (e.g., skipped features with null/invalid geometries) are shown in the dialog.

4. **View Results**:
   - Output layers (**Added**, **Deleted**, **Modified**) are added to the QGIS Layers panel.
   - Inspect the layers to analyze changes between the old and new datasets.

## License

This plugin is licensed under the **GNU General Public License v2.0 or later**. See the [LICENSE](https://github.com/AnustupJana/GeometryComparator-plugin/blob/main/LICENSE) file for details.

## Contact

- **Author**: Anustup Jana
- **Email**: anustupjana21@gmail.com
- **GitHub**: [Your GitHub Profile](https://github.com/AnustupJana)
