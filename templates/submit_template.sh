#!/bin/bash
#SBATCH --job-name={{JOBNAME}}_{{TIMESTAMP}}
#SBATCH --partition=tropshalab
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=32
#SBATCH --mem=256GB
#SBATCH --gres=gpu:1
#SBATCH --constraint=cuda-570.86.15
#SBATCH --time=1-00:00:00
#SBATCH --qos=gpu_access
#SBATCH --mail-type=ALL
#SBATCH --mail-user={{EMAIL}}
#SBATCH --output={{WORKDIR}}/logs/%x-%j.out

hostname
nvidia-smi

export AF3_INPUT_DIR={{WORKDIR}}
export AF3_OUTPUT_DIR={{WORKDIR}}/output

# Load Singularity and AF3 resources
module load singularity
export AF3_RESOURCES_DIR=/nas/longleaf/rhel8/apps/alphafold/3.0.1
export AF3_IMAGE=${AF3_RESOURCES_DIR}/image/alphafold3.0.1-cuda12.6-ubuntu22.04.sif
export AF3_CODE_DIR=${AF3_RESOURCES_DIR}/code
export AF3_MODEL_PARAMETERS_DIR=${AF3_RESOURCES_DIR}/weights
export AF3_DATABASES_DIR=/datacommons/alphafold/db_3.0.1

# Ensure output directory exists
mkdir -p $AF3_OUTPUT_DIR

# Run AlphaFold3 via Singularity
singularity exec \
    --nv \
    --bind $AF3_INPUT_DIR:/root/af_input \
    --bind $AF3_OUTPUT_DIR:/root/af_output \
    --bind $AF3_MODEL_PARAMETERS_DIR:/root/models \
    --bind $AF3_DATABASES_DIR:/root/public_databases \
    --bind $AF3_CODE_DIR:/root/code \
    $AF3_IMAGE \
    python /root/code/alphafold3/run_alphafold.py \
    --json_path=/root/af_input/input.json \
    --model_dir=/root/models \
    --db_dir=/root/public_databases \
    --output_dir=/root/af_output

# Package and clean up results
cd {{WORKDIR}}
ZIP_NAME="{{JOBNAME}}_{{TIMESTAMP}}.zip"
zip -r "${ZIP_NAME}" output/{{JOBNAME}}/
rm -rf output/
