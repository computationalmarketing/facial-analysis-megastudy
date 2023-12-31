## Facial Analysis

This repository contains code and data for paper
`A Megastudy on the Predictability of Personal Information from Facial Images` by Yegor Tkachenko and Kamel Jedidi published in Scientific Reports (2023). https://www.nature.com/articles/s41598-023-42054-9

Citation:

```
Tkachenko, Y., Jedidi, K. A megastudy on the predictability of personal information from facial images: Disentangling demographic and non-demographic signals. Sci Rep 13, 21073 (2023). https://doi.org/10.1038/s41598-023-42054-9
```

BibTeX:

```
@article{tkachenko2023megastudy,
  title={{A megastudy on the predictability of personal information from facial images: Disentangling demographic and non-demographic signals}},
  author={Tkachenko, Yegor and Jedidi, Kamel},
  journal={Scientific Reports},
  volume={13},
  number={1},
  pages={21073},
  year={2023}
}
```

Study participants have consented to the public release of their data (see `./questionnaire/study_survey.pdf` for the IRB consent form respondents had to complete before they could upload images and complete the questionnaire), Study data is provided with this repository at `./data.zip`.

## Running the code

To run this code, you will need python3.9 installed.

Step 0: Download this repository and within it set up a virtual environment: 

```
pip3 install virtualenv
python3.9 -m venv env
source env/bin/activate
```

Step 1: Install required package versions using command `pip3 install -r requirements.txt`

Step 2: Inside the working directory, where `study_results.py` is located, create a `models` directory -- download to it `resnet50_ft` weights from https://github.com/cydonia999/VGGFace2-pytorch as well as `utils.py` and `models/resnet.py` files from the same repository. 

Step 3: Install `pylbfgs` library via `https://bitbucket.org/rtaylor/pylbfgs/src/master/` by following instructions provided there. Prior to running `python setup.py install`, add the following three lines to `pylbfgs.c` file right after `param.linesearch = LBFGS_LINESEARCH_BACKTRACKING;` line (this enforces the right stopping condition):

```
param.max_linesearch = 100; 
param.past = 10;
param.delta = 1e-4;
```

Step 4: Unarchive `data.zip` file in the working directory (it should become a `data` folder).

Step 5: Run command `python3 ./study_results.py` from inside the working directory to replicate results from the paper.

## Notes

Full cross-validation as implemented in the code takes days to run when using a GPU (GeForce GTX 1080 Ti, CUDA 11.2, cuDNN 8.1.1). Folder `./results` contains computation output of the cross-validation in case you want to directly construct plots based on it. (You also need to unzip `./results/patch_importance.json.zip`).

Computed weights from L1 image decomposition are also provided in `feature_shadows_final.json.zip` (you need to unzip it).

Within `./data/data.csv`, `randomID` variable contains randomly generated unique identifier of a respondent in the data. There are 3 or fewer images -- and thus observations -- per respondent.

`q_to_full_name_dict` in `study_results.py` contains variable label definitions.

See the paper for further details.


Copyright (C) 2023 [Yegor Tkachenko](https://yegortkachenko.com), [Kamel Jedidi](https://www8.gsb.columbia.edu/cbs-directory/detail/kj7)
