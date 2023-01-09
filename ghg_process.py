
import argparse
import subprocess

import target_generation
import parallel_mf
import local_surface_control
import scale
import logging
from spectral.io import envi
import numpy as np
import os
from utils import envi_header
from osgeo import gdal



def main(input_args=None):
    parser = argparse.ArgumentParser(description="Robust MF")
    parser.add_argument('radiance_file', type=str,  metavar='INPUT', help='path to input image')   
    parser.add_argument('obs_file', type=str,  help='path to observation image')   
    parser.add_argument('loc_file', type=str,  help='path to location image')   
    parser.add_argument('glt_file', type=str,  help='path to glt image')   
    parser.add_argument('output_base', type=str,  help='output basepath for output image')    
    parser.add_argument('--state_subs', type=str, default=None,  help='state file from OE retrieval')    
    parser.add_argument('--overwrite', action='store_true',  help='state file from OE retrieval')    
    parser.add_argument('--loglevel', type=str, default='INFO', help='logging verbosity')    
    parser.add_argument('--logfile', type=str, default=None, help='output file to write log to')    
    parser.add_argument('--co2', action='store_true', help='flag to indicate whether to run co2')    
    args = parser.parse_args(input_args)

    irr_file = '/beegfs/scratch/brodrick/src/isofit/data/kurudz_0.1nm.dat'

    logging.basicConfig(format='%(levelname)s:%(asctime)s ||| %(message)s', level=args.loglevel,
                        filename=args.logfile, datefmt='%Y-%m-%d,%H:%M:%S')

    radiance_file = args.radiance_file
    radiance_file_hdr = envi_header(radiance_file)
 
    obs_file = args.obs_file
    obs_file_hdr = envi_header(obs_file)

    loc_file = args.loc_file
    loc_file_hdr = envi_header(loc_file)

    sza = envi.open(obs_file_hdr).open_memmap(interleave='bip')[...,4]
    mean_sza = np.mean(sza[sza != -9999])

    elevation = envi.open(loc_file_hdr).open_memmap(interleave='bip')[...,2]
    mean_elevation = np.mean(elevation[elevation != -9999]) / 1000.
    mean_elevation = min(max(0, mean_elevation),3)

    if args.state_subs is not None:
        state_ds = envi.open(envi_header(args.state_subs))
        band_names = state_ds.metadata['band names']
        h2o = state_ds.open_memmap(interleave='bip')[...,band_names.index('H2OSTR')]
        mean_h2o = np.mean(h2o[h2o != -9999])
    else:
        # Just guess something...
        mean_h2o = 1.3

    # Target
    co2_target_file = f'{args.output_base}_co2_target'
    ch4_target_file = f'{args.output_base}_ch4_target'

    # MF
    co2_mf_file = f'{args.output_base}_co2_mf'
    ch4_mf_file = f'{args.output_base}_ch4_mf'

    # MF - ORT
    co2_mf_ort_file = f'{args.output_base}_co2_mf_ort'
    ch4_mf_ort_file = f'{args.output_base}_ch4_mf_ort'

    # MF - Refined
    co2_mf_refined_file = f'{args.output_base}_co2_mf_refined'
    ch4_mf_refined_file = f'{args.output_base}_ch4_mf_refined'

    # MF - Refined - ORT
    co2_mf_refined_ort_file = f'{args.output_base}_co2_mf_refined_ort'
    ch4_mf_refined_ort_file = f'{args.output_base}_ch4_mf_refined_ort'
    
    # MF - Refined - ORT - Scaled
    co2_mf_refined_scaled_ort_file = f'{args.output_base}_co2_mf_refined_scaled_ort.tif'
    ch4_mf_refined_scaled_ort_file = f'{args.output_base}_ch4_mf_refined_scaled_ort.tif' ### CHANGE THIS NAME TO ch4_mf_refined_scaled_ort.tif

    # MF -  ORT - Scaled Color
    ch4_mf_scaled_color_ort_file = f'{args.output_base}_ch4_mf_scaled_color_ort.tif'  
    co2_mf_scaled_color_ort_file = f'{args.output_base}_co2_mf_scaled_color_ort.tif'

    # MF -  Refined - ORT - Scaled Color
    ch4_mf_refined_scaled_color_ort_file = f'{args.output_base}_ch4_mf_refined_scaled_color_ort.tif'
    co2_mf_refined_scaled_color_ort_file = f'{args.output_base}_co2_mf_refined_scaled_color_ort.tif'

    co2_mf_refined_kmz_file = f'{args.output_base}_co2_mf_refined.kmz'
    ch4_mf_refined_kmz_file = f'{args.output_base}_ch4_mf_refined.kmz'

    co2_mf_refined_color_kmz_file = f'{args.output_base}_co2_mf_refined_color.kmz'
    ch4_mf_refined_color_kmz_file = f'{args.output_base}_ch4_mf_refined_color.kmz'

    co2_mf_kmz_file = f'{args.output_base}_co2_mf.kmz'
    ch4_mf_kmz_file = f'{args.output_base}_ch4_mf.kmz'

    co2_mf_color_kmz_file = f'{args.output_base}_co2_mf_color.kmz'
    ch4_mf_color_kmz_file = f'{args.output_base}_ch4_mf_color.kmz'

    
    path = os.environ['PATH']
    path = path.replace('\Library\\bin;',':')
    os.environ['PATH'] = path

    if os.path.isfile(ch4_mf_file):
        dat = gdal.Open(ch4_mf_file).ReadAsArray()
        if np.all(dat == -9999):
            subprocess.call(f'rm {args.output_base}_ch4*',shell=True)


    if (os.path.isfile(co2_target_file) is False or args.overwrite) and args.co2:
        target_generation.main(['--co2', '-z', str(mean_sza), '-s', '100', '-g', str(mean_elevation), '-w', str(mean_h2o), '--output', co2_target_file, '--hdr', radiance_file_hdr])
    if os.path.isfile(ch4_target_file) is False or args.overwrite:
        target_generation.main(['--ch4', '-z', str(mean_sza), '-s', '100', '-g', str(mean_elevation), '-w', str(mean_h2o), '--output', ch4_target_file, '--hdr', radiance_file_hdr])


    if (os.path.isfile(co2_mf_file) is False or args.overwrite) and args.co2:
        parallel_mf.main([args.radiance_file, co2_target_file, co2_mf_file])
    
    print(os.path.isfile(ch4_mf_file))
    print(ch4_mf_file)
    if os.path.isfile(ch4_mf_file) is False or args.overwrite:
        print('starting parallel mf')
        parallel_mf.main([args.radiance_file, ch4_target_file, ch4_mf_file])

    if (os.path.isfile(co2_mf_refined_file) is False or args.overwrite) and args.co2:
        local_surface_control.main([co2_mf_file, args.radiance_file, args.loc_file, irr_file, co2_mf_refined_file, '--type', 'co2'])
    if os.path.isfile(ch4_mf_refined_file) is False or args.overwrite:
        local_surface_control.main([ch4_mf_file, args.radiance_file, args.loc_file, irr_file, ch4_mf_refined_file, '--type', 'ch4'])

    if (os.path.isfile(co2_mf_refined_ort_file) is False or args.overwrite) and args.co2:
        subprocess.call(f'python apply_glt.py {args.glt_file} {co2_mf_refined_file} {co2_mf_refined_ort_file}',shell=True)
    if os.path.isfile(ch4_mf_refined_ort_file) is False or args.overwrite:
        subprocess.call(f'python apply_glt.py {args.glt_file} {ch4_mf_refined_file} {ch4_mf_refined_ort_file}',shell=True)

    if (os.path.isfile(co2_mf_ort_file) is False or args.overwrite) and args.co2:
        subprocess.call(f'python apply_glt.py {args.glt_file} {co2_mf_file} {co2_mf_ort_file}',shell=True)
    if os.path.isfile(ch4_mf_ort_file) is False or args.overwrite:
        subprocess.call(f'python apply_glt.py {args.glt_file} {ch4_mf_file} {ch4_mf_ort_file}',shell=True)
    
    
    if os.path.isfile(ch4_mf_refined_scaled_ort_file) is False or args.overwrite:
        scale.main([ch4_mf_refined_ort_file, ch4_mf_refined_scaled_ort_file, '1', '500'])
    if (os.path.isfile(co2_mf_refined_scaled_ort_file) is False or args.overwrite) and args.co2:
        scale.main([co2_mf_refined_ort_file, co2_mf_refined_scaled_ort_file, '180', '11000'])

    if os.path.isfile(ch4_mf_refined_scaled_color_ort_file) is False or args.overwrite:
        scale.main([ch4_mf_refined_ort_file, ch4_mf_refined_scaled_color_ort_file, '1', '1000', '--cmap', 'plasma'])

    if os.path.isfile(ch4_mf_scaled_color_ort_file) is False or args.overwrite:
        scale.main([ch4_mf_ort_file, ch4_mf_scaled_color_ort_file, '1', '1000', '--cmap', 'plasma'])


    if os.path.isfile(ch4_mf_refined_kmz_file) is False or args.overwrite:
        hr_temp = f'{ch4_mf_refined_ort_file}_hrtemp'
        subprocess.call(f'gdalwarp -tr 0.00025 -0.00025 {ch4_mf_refined_scaled_ort_file} {hr_temp} -dstnodata 0',shell=True)
        subprocess.call(f'gdal_translate {hr_temp} {ch4_mf_refined_kmz_file} -a_nodata 0 -of KMLSUPEROVERLAY -co format=PNG',shell=True)
        subprocess.call(f'rm {hr_temp}',shell=True)

    if (os.path.isfile(co2_mf_refined_kmz_file) is False or args.overwrite) and args.co2:
        hr_temp = f'{co2_mf_refined_ort_file}_hrtemp'
        subprocess.call(f'gdalwarp -tr 0.00025 -0.00025 {co2_mf_refined_scaled_ort_file} {hr_temp} -dstnodata 0',shell=True)
        subprocess.call(f'gdal_translate {hr_temp} {co2_mf_refined_kmz_file} -a_nodata 0 -of KMLSUPEROVERLAY -co format=PNG',shell=True)
        subprocess.call(f'rm {hr_temp}',shell=True)


    if os.path.isfile(ch4_mf_refined_color_kmz_file) is False or args.overwrite:
        hr_temp = f'{ch4_mf_refined_ort_file}_hrtemp'
        subprocess.call(f'gdalwarp -tr 0.00025 -0.00025 {ch4_mf_refined_scaled_color_ort_file} {hr_temp} -dstnodata 0',shell=True)
        subprocess.call(f'gdal_translate {hr_temp} {ch4_mf_refined_color_kmz_file} -a_nodata 0 -of KMLSUPEROVERLAY -co format=PNG',shell=True)
        subprocess.call(f'rm {hr_temp}',shell=True)


    if os.path.isfile(ch4_mf_color_kmz_file) is False or args.overwrite:
        hr_temp = f'{ch4_mf_refined_ort_file}_hrtemp'
        subprocess.call(f'gdalwarp -tr 0.00025 -0.00025 {ch4_mf_scaled_color_ort_file} {hr_temp} -dstnodata 0',shell=True)
        subprocess.call(f'gdal_translate {hr_temp} {ch4_mf_color_kmz_file} -a_nodata 0 -of KMLSUPEROVERLAY -co format=PNG',shell=True)
        subprocess.call(f'rm {hr_temp}',shell=True)
 
    rdn_kmz = args.radiance_file.replace('.img','.kmz')
    dst_rdn_kmz = f'{args.output_base}_rdn_rgb.kmz'
    if os.path.isfile(rdn_kmz) and os.path.isfile(dst_rdn_kmz) is False:
        subprocess.call(f'cp {rdn_kmz} {dst_rdn_kmz}',shell=True)







if __name__ == '__main__':
    main()
