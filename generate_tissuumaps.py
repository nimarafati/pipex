import scanpy as sc
import scipy
import os
import json
import datetime
import sys

data_folder = os.environ.get('PIPEX_DATA')
include_marker_images = "no"
include_geojson = "no"
include_html = "no"

def exporting_tissuumaps ():
    if include_marker_images == "no" and include_geojson == "yes":
        print(">>> Impossible to display geojson without a background image", flush=True)
    
    adata = sc.read_h5ad(os.path.join(data_folder, 'analysis/downstream/anndata.h5ad'))

    # Make sure that the X matrix is in the compressed sparse column (CSC) format (required by TissUUmaps)
    adata.X = scipy.sparse.csc_matrix(adata.X)

    # Add image layers and cell segmentation geoJSON file to the AnnData object:
    if include_marker_images == "yes":
        markers = adata.var_names
    elif include_marker_images == "no":
        markers = []
    else:
        markers = [v for v in adata.var_names if v in include_marker_images.split(",")]
    if include_geojson == "yes" and include_marker_images != "no":
        regionFiles = [
            {
                "name": "Cell segmentation",
                "path": f"../cell_segmentation_geo.json",
                "title": "Cell segmentation",
                "settings":[
                    {
                        "module": "regionUtils",
                        "function": "_regionStrokeWidth",
                        "value": "0.5"
                    },
                    {
                        "module": "regionUtils",
                        "function": "_regionStrokeAdaptOnZoom",
                        "value": True
                    },
                    {
                        "module": "glUtils",
                        "function": "_regionShowOnTop",
                        "value": False
                    }
                ]
            }
        ]
    else:
        regionFiles = []
    adata.uns["tmap"] = json.dumps({
        "layers": [
            {
                "name": f"{marker}",
                "tileSource": f"../../{marker}.tif.dzi"
            }
            for marker in markers
        ],
        "regionFiles": regionFiles,
        "plugins": ["Feature_Space","InteractionQC","Spot_Inspector"],
        "settings": [
            {
                "module": "pluginUtils",
                "function": "startPlugin",
                "value": ["Spot_Inspector",
                [
                    {"name": "_layer_format", "value":"{layout-row6}"},
                    {"name": "_cmap", "value":"undefined"},
                ],False]
            },
            {
                "module": "pluginUtils",
                "function": "startPlugin",
                "value": ["InteractionQC",[],False]
            },
            {
                "module": "pluginUtils",
                "function": "startPlugin",
                "value": ["Feature_Space",[],False]
            }
        ],
    })
    adata.write_h5ad(os.path.join(data_folder, 'analysis/downstream/anndata_TissUUmaps.h5ad'))

    if include_html == "yes":
        import tissuumaps

        state = tissuumaps.read_h5ad.h5ad_to_tmap("", os.path.join(data_folder, 'analysis/downstream/anndata_TissUUmaps.h5ad'))
        tissuumaps.views.exportToStatic(
            json.dumps(state), 
            os.path.join(data_folder, 'analysis/downstream/TissUUmaps_webexport/'),
            os.path.join(data_folder, 'analysis/downstream')
        )
        from urllib.request import urlretrieve
        for plugin in ["Feature_Space","InteractionQC","Spot_Inspector"]:
            url = f"https://tissuumaps.github.io/TissUUmaps/plugins/latest/{plugin}.js"
            filename = os.path.join(data_folder, 'analysis/downstream/TissUUmaps_webexport/plugins/', f"{plugin}.js")
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            urlretrieve(url, filename)

#Function to handle the command line parameters passed
def options(argv):
    if (len(argv) == 0):
        print('export_tissuumaps.py arguments:\n\t-data=<optional /path/to/images/folder, defaults to /home/pipex/data> : example -> -data=/lab/projectX/images\n\t-include_marker_images=<yes or no or list of present specific markers to display as image layers> : example -> -include_marker_images=DAPI,SST,GORASP2\n\t-include_geojson=<yes or no to include cell segmentation as regions> : example -> -include_geojson=yes\n\t-include_html=<yes or no to export html page for sharing the TissUUmaps project on the web> : example -> -include_marker_images=yes', flush=True)
        sys.exit()
    else:
        for arg in argv:
            if arg.startswith('-help'):
                print('export_tissuumaps.py arguments:\n\t-data=<optional /path/to/images/folder, defaults to /home/pipex/data> : example -> -data=/lab/projectX/images\n\t-include_marker_images=<yes or no or list of present specific markers to display as image layers> : example -> -include_marker_images=DAPI,SST,GORASP2\n\t-include_geojson=<yes or no to include cell segmentation as regions> : example -> -include_geojson=yes\n\t-include_html=<yes or no to export html page for sharing the TissUUmaps project on the web> : example -> -include_marker_images=yes', flush=True)
                sys.exit()
            elif arg.startswith('-data='):
                global data_folder
                data_folder = arg[6:]
            elif arg.startswith('-include_marker_images='):
                global include_marker_images
                include_marker_images = arg[23:]
            elif arg.startswith('-include_geojson='):
                global include_geojson
                include_geojson = arg[17:]
            elif arg.startswith('-include_html='):
                global include_html
                include_html = arg[14:]

if __name__ =='__main__':
    options(sys.argv[1:])

    pidfile_filename = './RUNNING'
    if "PIPEX_WORK" in os.environ:
        pidfile_filename = './work/RUNNING'
    with open(pidfile_filename, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
        f.close()

    print(">>> Start time exporting tissuumaps =", datetime.datetime.now().strftime("%H:%M:%S"), flush=True)

    exporting_tissuumaps()

    print(">>> End time exporting tissuumaps =", datetime.datetime.now().strftime("%H:%M:%S"), flush=True)