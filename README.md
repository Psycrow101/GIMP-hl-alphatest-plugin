# Half-Life Alphatest for GIMP
The plugin converts the image to color indexing mode, moving the alpha channel colors as the last index in the palette. This allows to quickly prepare bitmap images as textures in alphatest mode for Half-Life game.

## Requirements
1. [GIMP](https://www.gimp.org/), recommended GIMP version >= 2.10.  
2. GIMP's python module gimpfu.  

## Installation
Download and extract the `hl-alphatest` folder to GIMP's `plug-ins` folder:  
	**Windows**: `C:\Users\<USERNAME>\AppData\Roaming\GIMP\2.10\plug-ins`  
	**Linux**: `/home/<USERNAME>/.config/GIMP/2.10/plug-ins`  
	**macOS**: `/Users/<USERNAME>/Library/Application Support/GIMP/2.10/plug-ins`

*If you can’t locate the `plug-ins` folder, open GIMP and go to Edit > Preferences > Folders > Plug-Ins and use one of the listed folders.*

## Usage
Go to Image > Half-Life > Alphatest and select the maximum alpha channel value for filtering and the dither type. This menu will be available only for images with transparent colors. If your image is already in indexed mode, switch to RGB mode (Image > Mode > RGB).

*After using the plugin, your layer groups will be merged.*

## See also
[GIMP plugin for import and export of Half-Life sprites (.spr)](https://github.com/Psycrow101/GIMP-hl-sprite-plugin)
