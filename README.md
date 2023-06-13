## Facial Analysis

This repository contains code and data for the working paper
`Yegor Tkachenko, Kamel Jedidi. A Megastudy on the Predictability of Personal Information from Facial Images (2023).`

Study participants have consented to the public release of their data (see `./questionnaire/study_survey.pdf` for the IRB consent form respondents had to complete before they could upload images and complete the questionnaire), Study data is provided with this repository at `./data.zip`.

## Running the code

To run this code, you will need python3 installed.

Step 1: Install current versions of all required packages using command `pip3 install -r requirements.txt`

Step 2: Inside the working drectory, where `study_results.py` is located, create a `models` directory -- download to it `resnet50_ft` weights from https://github.com/cydonia999/VGGFace2-pytorch as well as `utils.py` and `models/resnet.py` files from the same repository. 

Step 3: Install `pylbfgs` library via `https://bitbucket.org/rtaylor/pylbfgs/src/master/` by following instructions provided there. 

Step 4: Unarchive `data.zip` file in the working directory (it should become a `data` folder).

Step 5: Run command `python3 ./study_results.py` from inside this directory to replicate results from the paper.

## Notes

Full cross-validation as implemented in the code takes days to run when using a GPU. Folder `./results` contains computation output of the cross-validation in case you want to directly construct plots based on it. (You also need to unzip `./results/patch_importance.json.zip`).

Computed weights from L1 image decomposition are also provided in `feature_shadows_final.json.zip`.

Within `./data/data.csv`, `randomID` variable contains randomly generated unique identifier of a respondent in the data. There are 3 or fewer images -- and thus observations -- per respondent.

`q_to_full_name_dict` in `study_results.py` contains variable label definitions.

See the paper for further details.


Copyright (C) 2023 [Yegor Tkachenko](https://yegortkachenko.com), [Kamel Jedidi](https://www8.gsb.columbia.edu/cbs-directory/detail/kj7)
