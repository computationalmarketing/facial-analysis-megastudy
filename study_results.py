
# Copyright (C) 2023 Yegor Tkachenko, Kamel Jedidi
# Code -- A Megastudy on the Predictability of Personal Information From Facial Images

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick
import matplotlib.image as mpimg
from matplotlib import gridspec

from matplotlib import rcParams
rcParams.update({'font.size': 12})

rcParams['font.family'] = 'serif'
rcParams['font.sans-serif'] = ['Times']

import seaborn as sns

from textwrap import wrap

import torchvision.models as models
import torch
from torch.utils.data import DataLoader
from torch.autograd import Variable
import torch.nn.functional as F
import torch.optim as optim

import os
from os import walk
from tqdm import tqdm

from sklearn import metrics, svm
from sklearn.linear_model import BayesianRidge, LogisticRegression
from sklearn.decomposition import TruncatedSVD, PCA, FactorAnalysis
from sklearn.model_selection import KFold, GroupKFold, ShuffleSplit, GroupShuffleSplit
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import StandardScaler

import scipy.stats
from scipy.special import softmax
import scipy.cluster.hierarchy as sch
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.stats import ttest_ind

import json

import numpy as np

from torchvision import transforms
from torch.utils.data.dataset import Dataset
from PIL import Image
import pandas as pd

import pickle

from scipy import linalg



# fastdot
# https://gist.github.com/huyng/7969327#file-fastdot-py
def _force_forder(x):
    """
    Converts arrays x to fortran order. Returns
    a tuple in the form (x, is_transposed).
    """
    if x.flags.c_contiguous:
        return (x.T, True)
    else:
        return (x, False)
        
def fdot(A,B):
    """
    Uses blas libraries directly to perform dot product
    """
    
    A, trans_a = _force_forder(A)
    B, trans_b = _force_forder(B)
    gemm_dot = linalg.get_blas_funcs("gemm", arrays=(A,B))
    
    # gemm is implemented to compute: C = alpha*AB  + beta*C
    return gemm_dot(alpha=1.0, a=A, b=B, trans_a=trans_a, trans_b=trans_b)



'''
q_to_name_dict contains match between variable labels from the survey results file and a label of the variable
'''

q_to_name_dict = {#'Q11':'gender', #'Q12':'age', 'Q13':'race', 'Q14':'school',  # these variables expanded below
                        'Q15':'marital_status',
                        #'Q16':'employment', 
                        'Q17':'social_class', #'Q18':'religion', # NO VARIANCE, SO EXCLUDED 'Q19':'US_born',
                        'Q21':'body_fitness', #'Q22':'household_income', 'Q23':'zip_code', 
                        'Q24':'orientation',
                        #'Q25':'political_party', 
                        'Q26':'global_warming', 'Q27':'recycling', 'Q28':'religious',
                        'Q29':'offensive_ads_banned', 'Q30':'offensive_ads_brand',#'Q31':'facebook_evil', 
                        'Q32':'NRA_support',

                        'Q34':'bin_family_career', 'Q35':'bin_friendship_laws', 'Q36':'bin_freedom_truth',
                        'Q37':'bin_pleasure_duty', 'Q38':'bin_wealth_fame', 'Q39':'bin_politeness_honesty',
                        'Q40':'bin_beautiful_smart', 'Q41':'bin_belonging_independence',

                        'Q42_1': 'lfstl_set_routine', 
                        'Q42_4': 'lfstl_try_new_things', 
                        'Q42_5': 'lfstl_highly_social_many_friends',   
                        'Q42_6': 'lfstl_buy_new_before_others',
                        'Q42_7': 'lfstl_outgoing_soc_confident',
                        'Q42_8': 'lfstl_compulsive_purchases',  
                        'Q42_10': 'lfstl_political_protest_participation',  
                        'Q42_11': 'lfstl_donate_to_beggar',  
                        'Q42_12': 'lfstl_like_hunting',   
                        'Q42_13': 'lfstl_like_fishing',   
                        'Q42_14': 'lfstl_like_hiking',  
                        'Q42_15': 'lfstl_like_out_of_doors',
                        'Q42_16': 'lfstl_cabin_by_quiet_lake_spend_summer',  
                        'Q42_17': 'lfstl_good_fixing_mechanical_things',
                        'Q42_18': 'lfstl_repair_my_own_car',
                        'Q42_19': 'lfstl_like_war_stories',
                        'Q42_20': 'lfstl_do_better_than_avg_fist_fight',
                        'Q42_21': 'lfstl_would_want_to_be_prof_football_player',
                        'Q42_22': 'lfstl_would_like_to_be_policeman',  
                        'Q42_23': 'lfstl_too_much_violence_on_tv',  
                        'Q42_24': 'lfstl_should_be_gun_in_every_home',
                        'Q42_25': 'lfstl_like_danger', 
                        'Q42_26': 'lfstl_would_like_my_own_airplane',
                        'Q42_27': 'lfstl_like_to_play_poker',  
                        'Q42_28': 'lfstl_smoke_too_much',    
                        'Q42_29': 'lfstl_love_to_eat',
                        'Q42_30': 'lfstl_spend_money_on_myself_that_shuld_spend_on_family',  
                        'Q42_31': 'lfstl_if_given_chance_men_would_cheat_on_spouses',   
                        'Q42_33': 'lfstl_satisfied_with_life',  
                        'Q42_34': 'lfstl_like_to_be_in_charge',  
                        'Q42_35': 'lfstl_enjoy_shopping',  
                        'Q42_36': 'lfstl_plan_spending_carefully',  
                        'Q42_37': 'lfstl_obey_rules',

                        'Q43_1': 'lfstl_satisfied_with_weight',
                        'Q43_4': 'lfstl_regular_exercise_routine',
                        'Q43_5': 'lfstl_grew_up_eating_healthy_foods',
                        'Q43_7': 'lfstl_hard_to_be_disciplined_about_what_i_eat',
                        'Q43_9': 'lfstl_dont_have_to_worry_how_i_eat',
                        'Q43_11': 'lfstl_never_think_healthy_unhealthy_food',
                        'Q43_13': 'lfstl_stick_to_healthy_diet_for_family',
                        'Q43_14': 'lfstl_choose_snack_foods_that_give_vitamins_minerals',
                        
                        'Q44_1': 'lfstl_often_prepare_sauces_dips_from_scratch',
                        'Q44_5': 'lfstl_dont_have_much_interest_cooking',
                        'Q44_6': 'lfstl_seek_out_healthy_foods',
                        'Q44_8': 'lfstl_read_ingreadients_list_on_the_label',
                        'Q44_9': 'lfstl_looking_for_new_products_when_at_grocery_store',
                        'Q44_11': 'lfstl_lower_priced_products_same_as_higher_priced',
                        'Q44_13': 'lfstl_look_for_authentic_ingredients_flavors',
                        'Q44_14': 'lfstl_like_ethnic_foods',
                        'Q44_15': 'lfstl_daring_adventurous_trying_new_foods',

                        'Q45_42': 'brkfst_none',
                        'Q45_43': 'brkfst_bar',
                        'Q45_44': 'brkfst_fruit',
                        'Q45_45': 'brkfst_nuts',
                        'Q45_46': 'brkfst_regular_yogurt',
                        'Q45_47': 'brkfst_greek_yogurt',
                        'Q45_48': 'brkfst_muffin_croissant',
                        'Q45_49': 'brkfst_cold_cereal',
                        'Q45_50': 'brkfst_hot_cereal_oatmeal',
                        'Q45_51': 'brkfst_frozen_waffle',
                        'Q45_52': 'brkfst_cheese_cottage_cheese',
                        'Q45_53': 'brkfst_sandwhich',
                        'Q45_54': 'brkfst_salad',
                        'Q45_55': 'brkfst_eggs',
                        'Q45_56': 'brkfst_meat',
                        'Q45_57': 'brkfst_chicken',
                        'Q45_58': 'brkfst_fish',
                        'Q45_59': 'brkfst_potatoes',
                        'Q45_60': 'brkfst_vegetables',
                        'Q45_61': 'brkfst_soup',
                        'Q45_62': 'brkfst_pasta',
                        'Q45_63': 'brkfst_hummus',
                        'Q45_64': 'brkfst_bread_toast',
                        'Q45_65': 'brkfst_bagel_roll',
                        'Q45_66': 'brkfst_chocolate_candy',
                        'Q45_67': 'brkfst_cake_cookies',
                        'Q45_68': 'brkfst_chips',
                        'Q45_69': 'brkfst_crackers',
                        'Q45_70': 'brkfst_pretzels',
                        'Q45_71': 'brkfst_smoothie',
                        'Q45_72': 'brkfst_pastry_buns_fruit_pies',
                        'Q45_73': 'brkfst_brownies_snack_cakes',
                        'Q45_74': 'brkfst_popcorn',
                        'Q45_75': 'brkfst_ice_cream_sorbet',
                        'Q45_76': 'brkfst_pudding_gelatin',
                        'Q45_77': 'brkfst_refrig_dip_salsa_guacamole_dairy',
                        
                        'Q46_1': 'rsn_brkfst_gives_energy',
                        'Q46_4': 'rsn_brkfst_tide_over_next_meal',
                        'Q46_5': 'rsn_brkfst_great_taste',
                        'Q46_6': 'rsn_brkfst_satisfies_craving',
                        'Q46_7': 'rsn_brkfst_comforting_soothing',
                        'Q46_8': 'rsn_brkfst_healthy_good_guilt_free',
                        'Q46_9': 'rsn_brkfst_take_care_of_hunger_filling',
                        'Q46_10': 'rsn_brkfst_not_too_filling',
                        'Q46_11': 'rsn_brkfst_fits_with_who_i_am',
                        'Q46_12': 'rsn_brkfst_helps_relax_reduce_stress',
                        'Q46_13': 'rsn_brkfst_helps_control_weight',
                        'Q46_14': 'rsn_brkfst_helps_maintain_mental_focus', 
                        'Q46_15': 'rsn_brkfst_keeps_from_overeating_next_meal', 
                        'Q46_16': 'rsn_brkfst_great_texture', 
                        'Q46_17': 'rsn_brkfst_sweet_taste',
                        'Q46_18': 'rsn_brkfst_tangy_savory_taste',
                        'Q46_19': 'rsn_brkfst_chunky_multidim_texture',
                        'Q46_20': 'rsn_brkfst_smooth_creamy_texture',
                        'Q46_21': 'rsn_brkfst_gives_protein',
                        'Q46_22': 'rsn_brkfst_keeps_me_going',
                        'Q46_23': 'rsn_brkfst_good_food_to_eat_with_others',
                        'Q46_24': 'rsn_brkfst_keeps_me_on_track',
                        'Q46_25': 'rsn_brkfst_like_ingredients',
                        'Q46_26': 'rsn_brkfst_refreshing_taste',

                        'Q47':'pay_organic', 'Q48':'alcohol', 'Q49':'credit_score',

                        'Q50_1':'em_happiness', 'Q50_2':'em_stress', 'Q50_3':'em_loneliness',
                        'Q50_4':'em_jealousy', 'Q50_5':'em_fear', 'Q50_6':'em_hopefulness',
                        'Q50_7':'em_regret', 'Q50_8':'em_optimism', 'Q50_9':'em_contentness',
                        'Q50_10':'em_gratitude', 'Q50_11':'em_guilt', 'Q50_12':'em_anger',
                        'Q50_13':'em_joy', 'Q50_14':'em_contempt', 'Q50_15':'em_disgust',
                        'Q50_16':'em_sadness', 'Q50_17':'em_surprise', 'Q50_18':'em_vulnerability',
                        'Q50_19':'em_curiosity', 'Q50_20':'em_warmth',

                        'Q51':'entertain_freq', 'Q52_1':'post_lik_pos', 'Q52_2':'post_lik_neg', 
                        'Q53':'movie_activ_rec', 'Q54':'rec_lik_ask', 'Q55':'rec_lik_follow',

                        'Q56_1': 'bp_is_talkative',
                        'Q56_4': 'bp_tends_to_find_faults_with_others',   
                        'Q56_5': 'bp_does_thorough_job',  
                        'Q56_6': 'bp_is_depressed_blue',   
                        'Q56_7': 'bp_is_original_comes_up_new_ideas',   
                        'Q56_8': 'bp_is_helpful_unselfish',   
                        'Q56_9': 'bp_is_relaxed_handles_stress_well',   
                        'Q56_10': 'bp_is_curious_many_different_things',
                        'Q56_11': 'bp_is_full_of_energy',         
                        'Q56_12': 'bp_starts_quarrels_with_others',           
                        'Q56_13': 'bp_can_be_tense',
                        'Q56_14': 'bp_is_ingenious_deep_thinker',
                        'Q56_15': 'bp_has_forgiving_nature', 
                        'Q56_16': 'bp_tends_to_be_lazy',        
                        'Q56_17': 'bp_is_emotionally_stable_not_easily_upset',        
                        'Q56_18': 'bp_is_inventive',
                        'Q56_19': 'bp_has_assertive_personality',              
                        'Q56_20': 'bp_can_be_cold_aloof',           
                        'Q56_21': 'bp_perserveres_until_task_finished',               
                        'Q56_22': 'bp_can_be_moody',                 
                        'Q56_23': 'bp_values_artistic_aesthetic_experience',  
                        'Q56_24': 'bp_is_sometimes_shy_inhibited', 
                        'Q56_25': 'bp_is_considerate_kind_almost_everything',
                        'Q56_26': 'bp_does_things_efficiently', 
                        'Q56_27': 'bp_remains_calm_in_tense_situations',
                        'Q56_28': 'bp_prefers_routine_work', 
                        'Q56_29': 'bp_is_outgoing_sociable',
                        'Q56_30': 'bp_is_sometimes_rude_to_others', 
                        'Q56_31': 'bp_makes_plans_follows_through', 
                        'Q56_32': 'bp_gets_nervous_easily',
                        'Q56_33': 'bp_likes_to_reflect_play_with_ideas',
                        'Q56_39': 'bp_likes_to_cooperate_with_others', 
                        'Q56_40': 'bp_is_easily_distracted', 
                        'Q56_41': 'bp_is_sophisticated_arts_music_literature',  
                        'Q56_42': 'bp_generates_enthusiasm',  
                        'Q56_43': 'bp_is_reliable_worker', 
                        'Q56_44': 'bp_is_reserved',
                        'Q56_45': 'bp_can_be_somewhat_careless',
                        'Q56_46': 'bp_tends_to_be_disorganized',     
                        'Q56_47': 'bp_worries_a_lot',  
                        'Q56_48': 'bp_has_active_imagination',    
                        'Q56_49': 'bp_tends_to_be_quiet',  
                        'Q56_50': 'bp_is_generally_trusting',   
                        'Q56_52': 'bp_has_few_artistic_interests',

                        'Q57_1':'use_facebook', 'Q57_2':'use_twitter', 'Q57_3':'use_netflix',
                        'Q57_4':'use_spotify', 'Q57_5':'use_apple_music', 'Q57_6':'use_tinder',
                        'Q57_7':'use_pandora', 'Q57_9':'use_amazon',
                        'Q57_11':'use_saks', 'Q57_13':'use_dropbox',
                        'Q57_14':'use_gmail', 'Q57_15':'use_hotmail',
                        'Q57_16':'use_yahoo', 'Q57_18':'use_github',
                        'Q57_20':'use_shazam', 'Q57_21':'use_snapchat', 
                        'Q57_22':'use_whatsapp', 'Q57_23':'use_instagram', 
                        'Q57_24':'use_telegram', 'Q57_27':'use_hulu', 
                        'Q57_30':'use_bloomingdales', 'Q57_31':'use_NYT',
                        'Q57_32':'use_WSJ',

                        'Q59' : 'netflix_frequent_viewer',
                        'Q60' : 'netflix_binger',
                        'Q61' : 'netflix_active_recommender',
                        'Q62' : 'netflix_intend_to_get',

                        'Q63':'superbowl', 'Q64_1':'TV_news_trust', 'Q64_2':'Internet_news_trust',
                        'Q65':'track_news_daily', 'Q66':'read_reviews', #'Q67':'sports_programming',
                        'Q68':'social_media_time', 'Q69':'social_media_posting', #'Q70':'video_watching',

                        'Q73':'bin_iphone_galaxy', 'Q74':'bin_clothing_tech', 'Q75':'bin_brand_recogn_not',
                        'Q76':'bin_chocolate_strawberry', 'Q77':'bin_coke_original_diet', 
                        'Q78':'bin_coke_pepsi', 'Q79':'bin_club_book', 'Q80':'bin_beach_mountain',
                        'Q81':'bin_story_tell_listen', 'Q82':'bin_capitalism_socialism', 
                        'Q83':'bin_children_not', 'Q84':'bin_thinking_acting', 'Q85':'bin_planning_spontaneity',
                        'Q86':'bin_trump_hillary', 'Q87':'bin_madonna_lady_gaga', 'Q88':'bin_beatles_michael_jackson',

                        'Q89':'ec_past_fin_better', 'Q90':'ec_fut_fin_better', 'Q91':'ec_good_times',
                        'Q92':'ec_depression', 'Q93':'ec_buy',

                        'Q94_1' : 'price_bicycle',
                        'Q94_4' : 'price_smartphone',
                        'Q94_5' : 'price_laptop',
                        'Q94_6' : 'price_jeans',
                        'Q94_7' : 'price_sneakers',   
                        'Q94_8' : 'price_microwave', 
                        'Q94_9' : 'price_washing_machine', 
                        'Q94_10' : 'price_office_chair', 
                        
                        'Q95_1' : 'spend_savings_emergencies',
                        'Q95_3' : 'spend_necessities_bills',
                        'Q95_4' : 'spend_entertainment_gift_loved_one',

                        'Q97':'restaurant_ethics', 'Q99':'criminal_ethics', 'source':'data_source',

                        'Q11_0':'gender_0', 'Q11_1':'gender_1', 'Q11_2':'gender_2',
                        'Q12_0': 'age_0', 'Q12_1': 'age_1', 'Q12_2': 'age_2',
                        'Q13_0': 'race_0','Q13_1': 'race_1','Q13_2': 'race_2','Q13_3': 'race_3','Q13_4': 'race_4',
                        'Q14_0': 'school_0','Q14_1': 'school_1','Q14_2': 'school_2',
                        'Q16_0': 'employment_0','Q16_1': 'employment_1','Q16_2': 'employment_2',
                        'Q18_0': 'religion_0','Q18_1': 'religion_1','Q18_2': 'religion_2','Q18_3': 'religion_3',
                        'Q22_0': 'household_income_0','Q22_1': 'household_income_1', 'Q22_2': 'household_income_2',
                        'Q23_0': 'zip_code_0','Q23_1': 'zip_code_1', 'Q23_2':'zip_code_2','Q23_3': 'zip_code_3','Q23_4': 'zip_code_4',
                        'Q25_0': 'political_party_0','Q25_1': 'political_party_1','Q25_2': 'political_party_2',
                        'Q31_0': 'facebook_evil_0','Q31_1': 'facebook_evil_1', 'Q31_2': 'facebook_evil_2',
                        'Q67_0': 'sports_programming_0','Q67_1': 'sports_programming_1', 'Q67_2': 'sports_programming_2',
                        'Q70_0': 'video_watching_0', 'Q70_1': 'video_watching_1', 'Q70_2': 'video_watching_2',

                        'personality_extraversion':'personality_extraversion',
                        'personality_agreeableness':'personality_agreeableness',
                        'personality_conscientiousness':'personality_conscientiousness',
                        'personality_neuroticism':'personality_neuroticism',
                        'personality_openness':'personality_openness',

                        'Q71#1_1' : 'active_consumer_google_news',
                        'Q71#1_2' : 'active_consumer_yahoo_news',
                        'Q71#1_3' : 'active_consumer_new_york_times',
                        'Q71#1_4' : 'active_consumer_wsj',
                        'Q71#1_5' : 'active_consumer_boston_globe',
                        'Q71#1_6' : 'active_consumer_cnn',
                        'Q71#1_7' : 'active_consumer_huffpost',
                        'Q71#1_8' : 'active_consumer_foxnews',
                        'Q71#1_10' : 'active_consumer_vice',
                        'Q71#1_11' : 'active_consumer_chicago_tribune',
                        'Q71#1_12' : 'active_consumer_breitbart', 
                        'Q71#1_14' : 'active_consumer_washington_post', 
                        'Q71#1_16' : 'active_consumer_bbc_news',
                        'Q71#1_17' : 'active_consumer_facebook',
                        'Q71#1_19' : 'active_consumer_twitter',

                        'Q71#2_1' : 'bias_google_news',
                        'Q71#2_2' : 'bias_yahoo_news',
                        'Q71#2_3' : 'bias_new_york_times',
                        'Q71#2_4' : 'bias_wsj',
                        'Q71#2_5' : 'bias_boston_globe',
                        'Q71#2_6' : 'bias_cnn',
                        'Q71#2_7' : 'bias_huffpost',
                        'Q71#2_8' : 'bias_foxnews',
                        'Q71#2_10' : 'bias_vice',
                        'Q71#2_11' : 'bias_chicago_tribune',
                        'Q71#2_12' : 'bias_breitbart', 
                        'Q71#2_14' : 'bias_washington_post', 
                        'Q71#2_16' : 'bias_bbc_news',
                        'Q71#2_17' : 'bias_facebook',
                        'Q71#2_19' : 'bias_twitter',

                        'Q6_1_TEXT_0' : 'browser_safari_iphone',
                        'Q6_1_TEXT_1' : 'browser_chrome',
                        'Q6_1_TEXT_2' : 'browser_other',

                        }

image_metrics = {
                        'rc' : 'red_color', 
                        'gc' : 'green_color', 
                        'bc' : 'blue_color', 
                        'fwhr' : 'face_with_2_height_ratio', 
                        'fwidth' : 'face_width', 
                        'fheight': 'face_height', 
                        'sideeyeratio' : 'face_to_eye_left_right_ratio', 
                        'noseheight' : 'nose_height', 
                        'eyehdiff' : 'eye_height_difference', 
                        'intereyedist': 'inter_eye_difference', 
                        'lipwidth' : 'lip_width',
}
'''
q_to_full_name_dict is similar to q_to_name_dict and contains 
match between variable code from the survey results file and a full name of the variable -- used in plotting
'''

q_to_full_name_dict = {'Q15':'Marital status',
                     
                        'Q17':'Social class', 
                        'Q21':'Body fitness', 
                        'Q24':'Sexual orientation (non-hetero)',

                        'Q26':'Believes global warming is a threat', 
                        'Q27':'Makes effort to recycle', 
                        'Q28':'Considers himself religious',
                        'Q29':'Believes offensive ads should be banned', 
                        'Q30':'Will stop buying a brand accused of offensive advertising', 
                        'Q32':'Supports National Rifle Association (NRA)',

                        'Q34':'More important: Family vs. career', 
                        'Q35':'More important: Friendship vs. laws', 
                        'Q36':'More important: Freedom vs. truth',
                        'Q37':'More important: Pleasure vs. duty', 
                        'Q38':'More important: Wealth vs. fame', 
                        'Q39':'More important: Politeness vs. honesty',
                        'Q40':'More important: Being beautiful vs. being smart', 
                        'Q41':'More important: Belonging vs. independence',

                        # Lifestyle
                        'Q42_1': 'Lifestyle: Prefers a set routine', 
                        'Q42_4': 'Lifestyle: Likes to try new things', 
                        'Q42_5': 'Lifestyle: Is highly social with many friends',   
                        'Q42_6': 'Lifestyle: Buys new things before others',
                        'Q42_7': 'Lifestyle: Is outgoing and socially confident',
                        'Q42_8': 'Lifestyle: Tends to make compulsive purchases',  
                        'Q42_10': 'Lifestyle: Is likely to participate in a political protest',  
                        'Q42_11': 'Lifestyle: Is likely to donate to a beggar',  
                        'Q42_12': 'Lifestyle: Likes hunting',   
                        'Q42_13': 'Lifestyle: Likes fishing',   
                        'Q42_14': 'Lifestyle: Likes hiking',  
                        'Q42_15': 'Lifestyle: Likes out of doors',
                        'Q42_16': 'Lifestyle: Cabin by a quiet lake is a good way to spend summer',  
                        'Q42_17': 'Lifestyle: Is good at fixing mechanical things',
                        'Q42_18': 'Lifestyle: Repairs his own car',
                        'Q42_19': 'Lifestyle: Likes war stories',
                        'Q42_20': 'Lifestyle: Would do better than average in a fist fight',
                        'Q42_21': 'Lifestyle: Would want to be a professional football player',
                        'Q42_22': 'Lifestyle: Would like to be policeman',  
                        'Q42_23': 'Lifestyle: Thinks there is too much violence on TV',  
                        'Q42_24': 'Lifestyle: Believes there should be a gun in every home',
                        'Q42_25': 'Lifestyle: Likes danger', 
                        'Q42_26': 'Lifestyle: Would like his own airplane',
                        'Q42_27': 'Lifestyle: Likes to play poker',  
                        'Q42_28': 'Lifestyle: Smokes too much',    
                        'Q42_29': 'Lifestyle: Loves to eat',
                        'Q42_30': 'Lifestyle: Spends money on himself that should be spent on family',  
                        'Q42_31': 'Lifestyle: Believes that if given a chance men would cheat on spouses',   
                        'Q42_33': 'Lifestyle: Is satisfied with life',  
                        'Q42_34': 'Lifestyle: Likes to be in charge',  
                        'Q42_35': 'Lifestyle: Enjoys shopping',  
                        'Q42_36': 'Lifestyle: Plans spending carefully',  
                        'Q42_37': 'Lifestyle: Obeys rules',

                        'Q43_1': 'Food habits, attitudes: Is satisfied with his weight',
                        'Q43_4': 'Food habits, attitudes: Follows regular exercise routine',
                        'Q43_5': 'Food habits, attitudes: Grew up eating healthy foods',
                        'Q43_7': 'Food habits, attitudes: Finds it hard to be disciplined about what he eats',
                        'Q43_9': 'Food habits, attitudes: Does not have to worry about how he eats',
                        'Q43_11': 'Food habits, attitudes: Never thinks of healthy or unhealthy food',
                        'Q43_13': 'Food habits, attitudes: Sticks to healthy diet for his family',
                        'Q43_14': 'Food habits, attitudes:: Chooses snack foods that give vitamins and minerals',
                        
                        'Q44_1': 'Food habits, attitudes: Often prepares sauces, dips from scratch',
                        'Q44_5': 'Food habits, attitudes: Does not have much interest in cooking',
                        'Q44_6': 'Food habits, attitudes: Seeks out healthy foods',
                        'Q44_8': 'Food habits, attitudes: Reads ingredient list on the label',
                        'Q44_9': 'Food habits, attitudes: Looks for new products when at grocery store',
                        'Q44_11': 'Food habits, attitudes: Believes lower priced products are the same as higher priced ones',
                        'Q44_13': 'Food habits, attitudes: Look for authentic ingredients and flavors',
                        'Q44_14': 'Food habits, attitudes: Likes ethnic foods',
                        'Q44_15': 'Food habits, attitudes: Is daring, adventurous in trying new foods',

                        'Q45_42': 'Breakfast food choice: No breakfast',
                        'Q45_43': 'Breakfast food choice: Bar',
                        'Q45_44': 'Breakfast food choice: Fruit',
                        'Q45_45': 'Breakfast food choice: Nuts',
                        'Q45_46': 'Breakfast food choice: Regular yogurt',
                        'Q45_47': 'Breakfast food choice: Greek yogurt',
                        'Q45_48': 'Breakfast food choice: Muffin or croissant',
                        'Q45_49': 'Breakfast food choice: Cold cereal',
                        'Q45_50': 'Breakfast food choice: Hot cereal or oatmeal',
                        'Q45_51': 'Breakfast food choice: Frozen_waffle',
                        'Q45_52': 'Breakfast food choice: Cheese, cottage cheese',
                        'Q45_53': 'Breakfast food choice: Sandwich',
                        'Q45_54': 'Breakfast food choice: Salad',
                        'Q45_55': 'Breakfast food choice: Eggs',
                        'Q45_56': 'Breakfast food choice: Meat',
                        'Q45_57': 'Breakfast food choice: Chicken',
                        'Q45_58': 'Breakfast food choice: Fish',
                        'Q45_59': 'Breakfast food choice: Potatoes',
                        'Q45_60': 'Breakfast food choice: Vegetables',
                        'Q45_61': 'Breakfast food choice: Soup',
                        'Q45_62': 'Breakfast food choice: Pasta',
                        'Q45_63': 'Breakfast food choice: Hummus',
                        'Q45_64': 'Breakfast food choice: Bread, toast',
                        'Q45_65': 'Breakfast food choice: Bagel, roll',
                        'Q45_66': 'Breakfast food choice: Chocolate candy',
                        'Q45_67': 'Breakfast food choice: Cake, cookies',
                        'Q45_68': 'Breakfast food choice: Chips',
                        'Q45_69': 'Breakfast food choice: Crackers',
                        'Q45_70': 'Breakfast food choice: Pretzels',
                        'Q45_71': 'Breakfast food choice: Smoothie',
                        'Q45_72': 'Breakfast food choice: Pastry, buns, fruit pies',
                        'Q45_73': 'Breakfast food choice: Brownies, snack, cakes',
                        'Q45_74': 'Breakfast food choice: Popcorn',
                        'Q45_75': 'Breakfast food choice: Ice cream, sorbet',
                        'Q45_76': 'Breakfast food choice: Pudding, gelatin',
                        'Q45_77': 'Breakfast food choice: refrigerated dip (salsa, guacamole, dairy)',
                        
                        'Q46_1': 'Breakfast food choice motivations: Gives energy',
                        'Q46_4': 'Breakfast food choice motivations: Tides him over until next meal',
                        'Q46_5': 'Breakfast food choice motivations: Tastes great',
                        'Q46_6': 'Breakfast food choice motivations: Satisfies a craving',
                        'Q46_7': 'Breakfast food choice motivations: Is comforting, soothing',
                        'Q46_8': 'Breakfast food choice motivations: Healthy, good, guilt free',
                        'Q46_9': 'Breakfast food choice motivations: Takes care of hunger, is filling',
                        'Q46_10': 'Breakfast food choice motivations: Is not too filling',
                        'Q46_11': 'Breakfast food choice motivations: Fits with who he is',
                        'Q46_12': 'Breakfast food choice motivations: Helps relax, reduce stress',
                        'Q46_13': 'Breakfast food choice motivations: Helps control weight',
                        'Q46_14': 'Breakfast food choice motivations: Helps maintain mental focus', 
                        'Q46_15': 'Breakfast food choice motivations: Keeps from overeating during next meal', 
                        'Q46_16': 'Breakfast food choice motivations: Has great texture', 
                        'Q46_17': 'Breakfast food choice motivations: Tastes sweet',
                        'Q46_18': 'Breakfast food choice motivations: Tastes tangy, savory',
                        'Q46_19': 'Breakfast food choice motivations: Has chunky, multidimensional texture',
                        'Q46_20': 'Breakfast food choice motivations: Has smooth, creamy texture',
                        'Q46_21': 'Breakfast food choice motivations: Gives protein',
                        'Q46_22': 'Breakfast food choice motivations: Keeps him going',
                        'Q46_23': 'Breakfast food choice motivations: Is good food to eat with others',
                        'Q46_24': 'Breakfast food choice motivations: Keeps him on track',
                        'Q46_25': 'Breakfast food choice motivations: Likes ingredients',
                        'Q46_26': 'Breakfast food choice motivations: Has refreshing taste',

                        'Q47':'Is ready to pay more for organic food products', 
                        'Q48':'Is a frequent alcohol consumer', 
                        'Q49':'Missed a credit card payment within last year',

                        'Q50_1':'Regularly felt emotions: Happiness', 
                        'Q50_2':'Regularly felt emotions: Stress', 
                        'Q50_3':'Regularly felt emotions: Loneliness',
                        'Q50_4':'Regularly felt emotions: Jealousy', 
                        'Q50_5':'Regularly felt emotions: Fear', 
                        'Q50_6':'Regularly felt emotions: Hopefulness',
                        'Q50_7':'Regularly felt emotions: Regret', 
                        'Q50_8':'Regularly felt emotions: Optimism', 
                        'Q50_9':'Regularly felt emotions: Contentness',
                        'Q50_10':'Regularly felt emotions: Gratitude', 
                        'Q50_11':'Regularly felt emotions: Guilt', 
                        'Q50_12':'Regularly felt emotions: Anger',
                        'Q50_13':'Regularly felt emotions: Joy', 
                        'Q50_14':'Regularly felt emotions: Contempt', 
                        'Q50_15':'Regularly felt emotions: Disgust',
                        'Q50_16':'Regularly felt emotions: Sadness', 
                        'Q50_17':'Regularly felt emotions: Surprise', 
                        'Q50_18':'Regularly felt emotions: Vulnerability',
                        'Q50_19':'Regularly felt emotions: Curiosity', 
                        'Q50_20':'Regularly felt emotions: Warmth',

                        'Q51':'Frequency of entertaining others at home', 
                        'Q52_1':'Likelihood of social media post about positive shopping experience', 
                        'Q52_2':'Likelihood of social media post about negative shopping experience', 
                        'Q53':'Actively recommends movies to watch to friends', 
                        'Q54':'Likelihood of asking a friend for a movie recommendation', 
                        'Q55':'Likelihood of following a movie recommendation from a friend',

                        'Q56_1': 'Big 5 variable: Is talkative',
                        'Q56_4': 'Big 5 variable: Tends to find faults with others (reverse)',   
                        'Q56_5': 'Big 5 variable: Does thorough job',  
                        'Q56_6': 'Big 5 variable: Is depressed, blue',   
                        'Q56_7': 'Big 5 variable: Is original, comes up new ideas',   
                        'Q56_8': 'Big 5 variable: Is helpful, unselfish',   
                        'Q56_9': 'Big 5 variable: Is relaxed, handles stress well (reverse)',   
                        'Q56_10': 'Big 5 variable: Is curious about many different things',
                        'Q56_11': 'Big 5 variable: Is full of energy',         
                        'Q56_12': 'Big 5 variable: Starts quarrels with others (reverse)',           
                        'Q56_13': 'Big 5 variable: Can be tense',
                        'Q56_14': 'Big 5 variable: Is ingenious, deep thinker',
                        'Q56_15': 'Big 5 variable: Has forgiving nature', 
                        'Q56_16': 'Big 5 variable: Tends to be lazy (reverse)',        
                        'Q56_17': 'Big 5 variable: Is emotionally stable, not easily upset (reverse)',        
                        'Q56_18': 'Big 5 variable: Is inventive',
                        'Q56_19': 'Big 5 variable: Has assertive personality',              
                        'Q56_20': 'Big 5 variable: Can be cold, aloof (reverse)',           
                        'Q56_21': 'Big 5 variable: Perseveres until task is finished',               
                        'Q56_22': 'Big 5 variable: Can be moody',                 
                        'Q56_23': 'Big 5 variable: Values artistic, aesthetic experience',  
                        'Q56_24': 'Big 5 variable: Is sometimes shy, inhibited (reverse)', 
                        'Q56_25': 'Big 5 variable: Is considerate, kind to almost everyone',
                        'Q56_26': 'Big 5 variable: Does things efficiently', 
                        'Q56_27': 'Big 5 variable: Remains calm in tense situations (reverse)',
                        'Q56_28': 'Big 5 variable: Prefers routine work (reverse)', 
                        'Q56_29': 'Big 5 variable: Is outgoing, sociable',
                        'Q56_30': 'Big 5 variable: Is sometimes rude to others (reverse)', 
                        'Q56_31': 'Big 5 variable: Makes plans and follows through', 
                        'Q56_32': 'Big 5 variable: Gets nervous easily',
                        'Q56_33': 'Big 5 variable: Likes to reflect, play with ideas',
                        'Q56_39': 'Big 5 variable: Likes to cooperate with others', 
                        'Q56_40': 'Big 5 variable: Is easily distracted (reverse)', 
                        'Q56_41': 'Big 5 variable: Is sophisticated in arts, music, literature',  
                        'Q56_42': 'Big 5 variable: Generates enthusiasm',  
                        'Q56_43': 'Big 5 variable: Is reliable worker', 
                        'Q56_44': 'Big 5 variable: Is reserved (reverse)',
                        'Q56_45': 'Big 5 variable: Can be somewhat careless (reverse)',
                        'Q56_46': 'Big 5 variable: Tends to be disorganized (reverse)',     
                        'Q56_47': 'Big 5 variable: Worries a lot',  
                        'Q56_48': 'Big 5 variable: Has active imagination',    
                        'Q56_49': 'Big 5 variable: Tends to be quiet (reverse)',  
                        'Q56_50': 'Big 5 variable: Is generally trusting',   
                        'Q56_52': 'Big 5 variable: Has few artistic interests (reverse)',

                        'Q57_1':'Uses Facebook', 'Q57_2':'Uses Twitter', 'Q57_3':'Uses Netflix',
                        'Q57_4':'Uses Spotify', 'Q57_5':'Uses Apple music', 'Q57_6':'Uses Tinder',
                        'Q57_7':'Uses Pandora', 'Q57_9':'Uses Amazon',
                        'Q57_11':'Uses Saks', 'Q57_13':'Uses Dropbox',
                        'Q57_14':'Uses Gmail', 'Q57_15':'Uses Hotmail',
                        'Q57_16':'Uses Yahoo', 'Q57_18':'Uses Github',
                        'Q57_20':'Uses Shazam', 'Q57_21':'Uses Snapchat', 
                        'Q57_22':'Uses Whatsapp', 'Q57_23':'Uses Instagram', 
                        'Q57_24':'Uses Telegram', 'Q57_27':'Uses Hulu', 
                        'Q57_30':'Uses Bloomingdales', 'Q57_31':'Uses NYT',
                        'Q57_32':'Uses WSJ',

                        'Q59' : 'Watches Netflix 4 or more days per week',
                        'Q60' : 'Tends to watch more than 3 hours of Netflix at a time',
                        'Q61' : 'Likelihood of recommending Netflix to a friend',
                        'Q62' : 'Intent to get Netflix subscription within 6 months',

                        'Q63':'Perceived effect of Superbowl ads on choices', 
                        'Q64_1':'Trusts TV news', 
                        'Q64_2':'Trusts Internet news',
                        'Q65':'Tracks news daily', 
                        'Q66':'Reads product review in detail before purchase', #'Q67':'sports_programming',
                        'Q68':'Spends 4 hours or more a day on social media', 
                        'Q69':'Frequency of posting on social media', #'Q70':'video_watching',

                        'Q73':'Prefers: iPhone vs. Galaxy', 'Q74':'Prefers: Clothing vs. tech', 'Q75':'Prefers: Recognizable brand vs. not well-known brand',
                        'Q76':'Prefers: Chocolate ice cream vs. strawberry ice cream', 'Q77':'Prefers: Original coke vs. diet', 
                        'Q78':'Prefers: Coke vs. Pepsi', 'Q79':'Prefers: Night in club vs. night with a book', 'Q80':'Prefers: Beach vs. mountain',
                        'Q81':'Prefers: Telling a story vs. listening to a story', 'Q82':'Prefers: Capitalism vs. socialism', 
                        'Q83':'Prefers: Children vs. no children', 'Q84':'Prefers: Thinking vs. acting', 'Q85':'Prefers: Planning vs. spontaneity',
                        'Q86':'Prefers: Trump vs. Hillary', 'Q87':'Prefers: Madonna vs. Lady Gaga', 'Q88':'Prefers: Beatles vs. Michael Jackson',

                        'Q89':'Is better/ worse financially than a year before', 
                        'Q90':'Expects to be better/ worse financially in a year', 
                        'Q91':'Expects good/ bad times financially in the US within a year',
                        'Q92':'Expects economic depression in the next five years', 
                        'Q93':'Considers it to be a good time to buy a major household item',

                        'Q94_1' : 'Price sensitivity: Bicycle',
                        'Q94_4' : 'Price sensitivity: Smartphone',
                        'Q94_5' : 'Price sensitivity: Laptop',
                        'Q94_6' : 'Price sensitivity: Jeans',
                        'Q94_7' : 'Price sensitivity: Sneakers',   
                        'Q94_8' : 'Price sensitivity: Microwave', 
                        'Q94_9' : 'Price sensitivity: Washing machine', 
                        'Q94_10' : 'Price sensitivity: Office chair', 
                        
                        'Q95_1' : 'Windfall income allocation: Savings, emergencies',
                        'Q95_3' : 'Windfall income allocation: Necessities, bills',
                        'Q95_4' : 'Windfall income allocation: Gift to a loved one',

                        'Q97':'Ethics: What right does your friend have to expect you to go easy on her restaurant in your review?', 
                        'Q99':'Ethics: What right does your friend have to expect you to lie in court to protect him?', 

                        'source':'Data source: Qualtrics panel vs. MTurk',

                        'Q11_0': 'Gender: Male', 'Q11_1':'Gender: Female', 'Q11_2':'Gender: Other',
                        'Q12_0': 'Age: <=30', 'Q12_1': 'Age: (30; 50] ', 'Q12_2': 'Age: > 50',
                        'Q13_0': 'Race: Caucasian/ White', 'Q13_1': 'Race: Asian','Q13_2': 'Race: Hispanic/ Latino','Q13_3': 'Race: African American/ Black','Q13_4': 'Race: Other',
                        'Q14_0': 'Education achieved: High school or less','Q14_1': 'Education achieved: Undergraduate degree','Q14_2': 'Education achieved: Graduate degree',
                        'Q16_0': 'Employment: Employed/ student','Q16_1': 'Employment: Unemployed, but looking','Q16_2': 'Employment: Unemployed and not looking',
                        'Q18_0': 'Religious background: Christianity','Q18_1': 'Religious background: Judaism, Islam','Q18_2': 'Religious background: Other (Hinduism, Buddhism, etc.)','Q18_3': 'Religious background: No particular religion',
                        'Q22_0': 'Household income: <$50K','Q22_1': 'Household income: [$50K,$100K)', 'Q22_2': 'Household income: >=$100K',
                        'Q23_0': 'ZIP code first digit: 0, 1','Q23_1': 'ZIP code first digit: 2, 3', 'Q23_2':'ZIP code first digit: 4, 5','Q23_3': 'ZIP code first digit: 6, 7','Q23_4': 'ZIP code first digit: 8, 9',
                        'Q25_0': 'Political party alignment: Republican','Q25_1': 'Political party alignment: Democrat','Q25_2': 'Political party alignment: Independent',
                        'Q31_0': 'Facebook is good for humanity: Yes','Q31_1': 'Facebook is good for humanity: No', 'Q31_2': 'Facebook is good for humanity: Unsure',
                        'Q67_0': 'Sports programming hours watched per week: 0','Q67_1': 'Sports programming hours watched per week: (0,8]', 'Q67_2': 'Sports programming hours watched per week: >8',
                        'Q70_0': 'Prefers to watch videos: Online', 'Q70_1': 'Prefers to watch videos: TV', 'Q70_2': 'Prefers to watch videos: Does not watch videos',

                        'personality_extraversion':'Big 5 personality: Extraversion',
                        'personality_agreeableness':'Big 5 personality: Agreeableness',
                        'personality_conscientiousness':'Big 5 personality: Conscientiousness',
                        'personality_neuroticism':'Big 5 personality: Neuroticism',
                        'personality_openness':'Big 5 personality: Openness',

                        'Q71#1_1' : 'Active consumer: Google news',
                        'Q71#1_2' : 'Active consumer: Yahoo news',
                        'Q71#1_3' : 'Active consumer: New York Times',
                        'Q71#1_4' : 'Active consumer: WSJ',
                        'Q71#1_5' : 'Active consumer: Boston Globe',
                        'Q71#1_6' : 'Active consumer: CNN',
                        'Q71#1_7' : 'Active consumer: Huffpost',
                        'Q71#1_8' : 'Active consumer: FoxNews',
                        'Q71#1_10' : 'Active consumer: Vice',
                        'Q71#1_11' : 'Active consumer: Chicago Tribune',
                        'Q71#1_12' : 'Active consumer: Breitbart', 
                        'Q71#1_14' : 'Active consumer: Washington Post', 
                        'Q71#1_16' : 'Active consumer: BBC News',
                        'Q71#1_17' : 'Active consumer: Facebook',
                        'Q71#1_19' : 'Active consumer: Twitter',

                        'Q71#2_1' : 'Perception of bias: Google News',
                        'Q71#2_2' : 'Perception of bias: Yahoo News',
                        'Q71#2_3' : 'Perception of bias: New York Times',
                        'Q71#2_4' : 'Perception of bias: WSJ',
                        'Q71#2_5' : 'Perception of bias: Boston Globe',
                        'Q71#2_6' : 'Perception of bias: CNN',
                        'Q71#2_7' : 'Perception of bias: Huffpost',
                        'Q71#2_8' : 'Perception of bias: FoxNews',
                        'Q71#2_10' : 'Perception of bias: Vice',
                        'Q71#2_11' : 'Perception of bias: Chicago Tribune',
                        'Q71#2_12' : 'Perception of bias: Breitbart', 
                        'Q71#2_14' : 'Perception of bias: Washington Post', 
                        'Q71#2_16' : 'Perception of bias: BBC News',
                        'Q71#2_17' : 'Perception of bias: Facebook',
                        'Q71#2_19' : 'Perception of bias: Twitter',

                        'Q6_1_TEXT_0' : 'Browser: Safari iPhone',
                        'Q6_1_TEXT_1' : 'Browser: Chrome',
                        'Q6_1_TEXT_2' : 'Browser: Other',

                        # 'rc' : 'Color channel: Red', 
                        # 'gc' : 'Color channel: Green', 
                        # 'bc' : 'Color channel: Blue', 
                        # 'fwhr' : 'Face width-to-height ratio', 
                        # 'fwidth' : 'Face width', 
                        # 'fheight': 'Face height', 
                        # 'sideeyeratio' : 'Face-edge to eye distance, left to right ratio', 
                        # 'noseheight' : 'Nose height', 
                        # 'eyehdiff' : 'Eye height difference', 
                        # 'intereyedist': 'Inter-eye difference', 
                        # 'lipwidth' : 'Lip width',
                        }

'''
var_groups contains a grouping of variables by categories we identified
some variables, such as data source (qualtrics vs. mturk) are not included in the grouping
'''

var_groups = {
                'demographics_biological' : [
                              'Q11_1', # gender
                              'Q12_0', 'Q12_1', # age
                              'Q13_0','Q13_1', 'Q13_2','Q13_3', # race
                              'Q21', # body fitness
                              'Q24',# orientation
                              # 'rc', 'gc', 'bc',# avg. face color
                              # 'fwhr', 'fwidth', 'fheight', 
                              #   'sideeyeratio', 'noseheight', 'eyehdiff', 'intereyedist', 'lipwidth'
                                ], 
                  
                  'demographics_socio_economic' : [
                              'Q15', # :'marital_status'
                              'Q17', #:'social_class'
                              'Q14_0', 'Q14_1', # school level
                              'Q16_0', 'Q16_1', # employment status
                              'Q18_0','Q18_1','Q18_2', # religious
                              'Q22_0', 'Q22_1', # household income                        
                              'Q23_0','Q23_1', 'Q23_2','Q23_3', # zip code
                              'Q25_0', 'Q25_1'], # political party

                    'personality' : ['personality_extraversion',
                        'personality_agreeableness',
                        'personality_conscientiousness',
                        'personality_neuroticism',
                        'personality_openness'
                    ],

                    'character_ethics' : [
                        'Q97', #'restaurant_ethics'
                        'Q99', #'criminal_ethics'
                        'Q49', #'credit_score',
                        'Q48', #'alcohol', 
                    ],

                    'lifestyle' : [
                        'Q42_1',#: 'lfstl_set_routine', 
                        'Q42_4',#: 'lfstl_try_new_things', 
                        'Q42_5',#: 'lfstl_highly_social_many_friends',   
                        'Q42_6',#: 'lfstl_buy_new_before_others',
                        'Q42_7',#: 'lfstl_outgoing_soc_confident',
                        'Q42_8',#: 'lfstl_compulsive_purchases',  
                        'Q42_10',#: 'lfstl_political_protest_participation',  
                        'Q42_11',#: 'lfstl_donate_to_beggar',  
                        'Q42_12',#: 'lfstl_like_hunting',   
                        'Q42_13',#: 'lfstl_like_fishing',   
                        'Q42_14',#: 'lfstl_like_hiking',  
                        'Q42_15',#: 'lfstl_like_out_of_doors',
                        'Q42_16',#: 'lfstl_cabin_by_quiet_lake_spend_summer',  
                        'Q42_17',#: 'lfstl_good_fixing_mechanical_things',
                        'Q42_18',#: 'lfstl_repair_my_own_car',
                        'Q42_19',#: 'lfstl_like_war_stories',
                        'Q42_20',#: 'lfstl_do_better_than_avg_fist_fight',
                        'Q42_21',#: 'lfstl_would_want_to_be_prof_football_player',
                        'Q42_22',#: 'lfstl_would_like_to_be_policeman',  
                        'Q42_23',#: 'lfstl_too_much_violence_on_tv',  
                        'Q42_24',#: 'lfstl_should_be_gun_in_every_home',
                        'Q42_25',#: 'lfstl_like_danger', 
                        'Q42_26',#: 'lfstl_would_like_my_own_airplane',
                        'Q42_27',#: 'lfstl_like_to_play_poker',  
                        'Q42_28',#: 'lfstl_smoke_too_much',    
                        'Q42_29',#: 'lfstl_love_to_eat',
                        'Q42_30',#: 'lfstl_spend_money_on_myself_that_shuld_spend_on_family',  
                        'Q42_31',#: 'lfstl_if_given_chance_men_would_cheat_on_spouses',   
                        'Q42_33',#: 'lfstl_satisfied_with_life',  
                        'Q42_34',#: 'lfstl_like_to_be_in_charge',  
                        'Q42_35',#: 'lfstl_enjoy_shopping',  
                        'Q42_36',#: 'lfstl_plan_spending_carefully',  
                        'Q42_37',#: 'lfstl_obey_rules',
                        ],

                    'food_habits_and_attitudes' : [
                        'Q43_1',#: 'lfstl_satisfied_with_weight',
                        'Q43_4',#: 'lfstl_regular_exercise_routine',
                        'Q43_5',#: 'lfstl_grew_up_eating_healthy_foods',
                        'Q43_7',#: 'lfstl_hard_to_be_disciplined_about_what_i_eat',
                        'Q43_9',#: 'lfstl_dont_have_to_worry_how_i_eat',
                        'Q43_11',#: 'lfstl_never_think_healthy_unhealthy_food',
                        'Q43_13',#: 'lfstl_stick_to_healthy_diet_for_family',
                        'Q43_14',#: 'lfstl_choose_snack_foods_that_give_vitamins_minerals',
                        
                        'Q44_1',#: 'lfstl_often_prepare_sauces_dips_from_scratch',
                        'Q44_5',#: 'lfstl_dont_have_much_interest_cooking',
                        'Q44_6',#: 'lfstl_seek_out_healthy_foods',
                        'Q44_8',#: 'lfstl_read_ingreadients_list_on_the_label',
                        'Q44_9',#: 'lfstl_looking_for_new_products_when_at_grocery_store',
                        'Q44_11',#: 'lfstl_lower_priced_products_same_as_higher_priced',
                        'Q44_13',#: 'lfstl_look_for_authentic_ingredients_flavors',
                        'Q44_14',#: 'lfstl_like_ethnic_foods',
                        'Q44_15',#: 'lfstl_daring_adventurous_trying_new_foods',

                        'Q47',#:'pay_organic', 
                        ],

                    'emotional_state' : [
                        'Q50_1',#:'em_happiness', 
                        'Q50_2',#:'em_stress', 
                        'Q50_3',#:'em_loneliness',
                        'Q50_4',#:'em_jealousy', 
                        'Q50_5',#:'em_fear', 
                        'Q50_6',#:'em_hopefulness',
                        'Q50_7',#:'em_regret', 
                        'Q50_8',#:'em_optimism', 
                        'Q50_9',#:'em_contentness',
                        'Q50_10',#:'em_gratitude', 
                        'Q50_11',#:'em_guilt', 
                        'Q50_12',#:'em_anger',
                        'Q50_13',#:'em_joy', 
                        'Q50_14',#:'em_contempt', 
                        'Q50_15',#:'em_disgust',
                        'Q50_16',#:'em_sadness', 
                        'Q50_17',#:'em_surprise', 
                        'Q50_18',#:'em_vulnerability',
                        'Q50_19',#:'em_curiosity', 
                        'Q50_20',#:'em_warmth'
                        ],

                    'values_and_beliefs' : [
                        
                        'Q26',#:'global_warming', 
                        'Q27',#:'recycling', 
                        'Q28',#:'religious',
                        'Q29',#:'offensive_ads_banned', 
                        'Q30',#:'offensive_ads_brand',
                        'Q32',#:'NRA_support',

                        'Q31_0',#: 'facebook_evil_0',
                        'Q31_1',#: 'facebook_evil_1', 
                        'Q31_2',#: 'facebook_evil_2',

                        'Q34',#:'bin_family_career', 
                        'Q35',#:'bin_friendship_laws', 
                        'Q36',#:'bin_freedom_truth',
                        'Q37',#:'bin_pleasure_duty', 
                        'Q38',#:'bin_wealth_fame', 
                        'Q39',#:'bin_politeness_honesty',
                        'Q40',#:'bin_beautiful_smart', 
                        'Q41',#:'bin_belonging_independence',
                        
                        ],
                    
                    'price_sensitivity' : [                        
                        'Q94_1',# : 'price_bicycle',
                        'Q94_4',# : 'price_smartphone',
                        'Q94_5',# : 'price_laptop',
                        'Q94_6',# : 'price_jeans',
                        'Q94_7',# : 'price_sneakers',   
                        'Q94_8',# : 'price_microwave', 
                        'Q94_9',# : 'price_washing_machine', 
                        'Q94_10',# : 'price_office_chair', 
                        ],

                    'breakfast_food_choice' : [
                        'Q45_42',#: 'brkfst_none',
                        'Q45_43',#: 'brkfst_bar',
                        'Q45_44',#: 'brkfst_fruit',
                        'Q45_45',#: 'brkfst_nuts',
                        'Q45_46',#: 'brkfst_regular_yogurt',
                        'Q45_47',#: 'brkfst_greek_yogurt',
                        'Q45_48',#: 'brkfst_muffin_croissant',
                        'Q45_49',#: 'brkfst_cold_cereal',
                        'Q45_50',#: 'brkfst_hot_cereal_oatmeal',
                        'Q45_51',#: 'brkfst_frozen_waffle',
                        'Q45_52',#: 'brkfst_cheese_cottage_cheese',
                        'Q45_53',#: 'brkfst_sandwhich',
                        'Q45_54',#: 'brkfst_salad',
                        'Q45_55',#: 'brkfst_eggs',
                        'Q45_56',#: 'brkfst_meat',
                        'Q45_57',#: 'brkfst_chicken',
                        'Q45_58',#: 'brkfst_fish',
                        'Q45_59',#: 'brkfst_potatoes',
                        'Q45_60',#: 'brkfst_vegetables',
                        'Q45_61',#: 'brkfst_soup',
                        'Q45_62',#: 'brkfst_pasta',
                        'Q45_63',#: 'brkfst_hummus',
                        'Q45_64',#: 'brkfst_bread_toast',
                        'Q45_65',#: 'brkfst_bagel_roll',
                        'Q45_66',#: 'brkfst_chocolate_candy',
                        'Q45_67',#: 'brkfst_cake_cookies',
                        'Q45_68',#: 'brkfst_chips',
                        'Q45_69',#: 'brkfst_crackers',
                        'Q45_70',#: 'brkfst_pretzels',
                        'Q45_71',#: 'brkfst_smoothie',
                        'Q45_72',#: 'brkfst_pastry_buns_fruit_pies',
                        'Q45_73',#: 'brkfst_brownies_snack_cakes',
                        'Q45_74',#: 'brkfst_popcorn',
                        'Q45_75',#: 'brkfst_ice_cream_sorbet',
                        'Q45_76',#: 'brkfst_pudding_gelatin',
                        'Q45_77',#: 'brkfst_refrig_dip_salsa_guacamole_dairy',
                    ],

                    'breakfast_motivations' : [
                        'Q46_1',#: 'rsn_brkfst_gives_energy',
                        'Q46_4',#: 'rsn_brkfst_tide_over_next_meal',
                        'Q46_5',#: 'rsn_brkfst_great_taste',
                        'Q46_6',#: 'rsn_brkfst_satisfies_craving',
                        'Q46_7',#: 'rsn_brkfst_comforting_soothing',
                        'Q46_8',#: 'rsn_brkfst_healthy_good_guilt_free',
                        'Q46_9',#: 'rsn_brkfst_take_care_of_hunger_filling',
                        'Q46_10',#: 'rsn_brkfst_not_too_filling',
                        'Q46_11',#: 'rsn_brkfst_fits_with_who_i_am',
                        'Q46_12',#: 'rsn_brkfst_helps_relax_reduce_stress',
                        'Q46_13',#: 'rsn_brkfst_helps_control_weight',
                        'Q46_14',#: 'rsn_brkfst_helps_maintain_mental_focus', 
                        'Q46_15',#: 'rsn_brkfst_keeps_from_overeating_next_meal', 
                        'Q46_16',#: 'rsn_brkfst_great_texture', 
                        'Q46_17',#: 'rsn_brkfst_sweet_taste',
                        'Q46_18',#: 'rsn_brkfst_tangy_savory_taste',
                        'Q46_19',#: 'rsn_brkfst_chunky_multidim_texture',
                        'Q46_20',#: 'rsn_brkfst_smooth_creamy_texture',
                        'Q46_21',#: 'rsn_brkfst_gives_protein',
                        'Q46_22',#: 'rsn_brkfst_keeps_me_going',
                        'Q46_23',#: 'rsn_brkfst_good_food_to_eat_with_others',
                        'Q46_24',#: 'rsn_brkfst_keeps_me_on_track',
                        'Q46_25',#: 'rsn_brkfst_like_ingredients',
                        'Q46_26',#: 'rsn_brkfst_refreshing_taste',
                        ],

                    'product_preferences' : [
                        'Q73',#:'bin_iphone_galaxy', 
                        'Q74',#:'bin_clothing_tech', 
                        'Q75',#:'bin_brand_recogn_not',
                        'Q76',#:'bin_chocolate_strawberry', 
                        'Q77',#:'bin_coke_original_diet', 
                        'Q78',#:'bin_coke_pepsi', 
                        'Q79',#:'bin_club_book', 
                        'Q80',#:'bin_beach_mountain',
                        'Q81',#:'bin_story_tell_listen', 
                        'Q82',#:'bin_capitalism_socialism', 
                        'Q83',#:'bin_children_not', 
                        'Q84',#:'bin_thinking_acting', 
                        'Q85',#:'bin_planning_spontaneity',
                        'Q86',#:'bin_trump_hillary', 
                        'Q87',#:'bin_madonna_lady_gaga', 
                        'Q88',#:'bin_beatles_michael_jackson',
                    ],

                    'online_service_usage' : [
                        'Q57_1',#:'use_facebook', 
                        'Q57_2',#:'use_twitter', 
                        'Q57_3',#:'use_netflix',
                        'Q57_4',#:'use_spotify', 
                        'Q57_5',#:'use_apple_music', 
                        'Q57_6',#:'use_tinder',
                        'Q57_7',#:'use_pandora', 
                        'Q57_9',#:'use_amazon',
                        'Q57_11',#:'use_saks', 
                        'Q57_13',#:'use_dropbox',
                        'Q57_14',#:'use_gmail', 
                        'Q57_15',#:'use_hotmail',
                        'Q57_16',#:'use_yahoo', 
                        'Q57_18',#:'use_github',
                        'Q57_20',#:'use_shazam', 
                        'Q57_21',#:'use_snapchat', 
                        'Q57_22',#:'use_whatsapp', 
                        'Q57_23',#:'use_instagram', 
                        'Q57_24',#:'use_telegram', 
                        'Q57_27',#:'use_hulu', 
                        'Q57_30',#:'use_bloomingdales', 
                        'Q57_31',#:'use_NYT',
                        'Q57_32',#:'use_WSJ',
                    ],

                    'browser' : [
                        'Q6_1_TEXT_0', #: 'Browser: Safari iPhone',
                        'Q6_1_TEXT_1', #: 'Browser: Chrome',
                        'Q6_1_TEXT_2', #: 'Browser: Other',
                        ],

                    'media_source' : [
                        'Q71#1_1',# : 'active_consumer_google_news',
                        'Q71#1_2',# : 'active_consumer_yahoo_news',
                        'Q71#1_3',# : 'active_consumer_new_york_times',
                        'Q71#1_4',# : 'active_consumer_wsj',
                        'Q71#1_5',# : 'active_consumer_boston_globe',
                        'Q71#1_6',# : 'active_consumer_cnn',
                        'Q71#1_7',# : 'active_consumer_huffpost',
                        'Q71#1_8',# : 'active_consumer_foxnews',
                        'Q71#1_10',# : 'active_consumer_vice',
                        'Q71#1_11',# : 'active_consumer_chicago_tribune',
                        'Q71#1_12',# : 'active_consumer_breitbart', 
                        'Q71#1_14',# : 'active_consumer_washington_post', 
                        'Q71#1_16',# : 'active_consumer_bbc_news',
                        'Q71#1_17',# : 'active_consumer_facebook',
                        'Q71#1_19',# : 'active_consumer_twitter',
                    ],

                    'media_trust' : [
                        'Q71#2_1',# : 'bias_google_news',
                        'Q71#2_2',# : 'bias_yahoo_news',
                        'Q71#2_3',# : 'bias_new_york_times',
                        'Q71#2_4',# : 'bias_wsj',
                        'Q71#2_5',# : 'bias_boston_globe',
                        'Q71#2_6',# : 'bias_cnn',
                        'Q71#2_7',# : 'bias_huffpost',
                        'Q71#2_8',# : 'bias_foxnews',
                        'Q71#2_10',# : 'bias_vice',
                        'Q71#2_11',# : 'bias_chicago_tribune',
                        'Q71#2_12',# : 'bias_breitbart', 
                        'Q71#2_14',# : 'bias_washington_post', 
                        'Q71#2_16',# : 'bias_bbc_news',
                        'Q71#2_17',# : 'bias_facebook',
                        'Q71#2_19',# : 'bias_twitter',

                        'Q64_1',#:'TV_news_trust', 
                        'Q64_2',#:'Internet_news_trust',

                    ],

                    'economic_outlook' : [
                        'Q89',#:'ec_past_fin_better', 
                        'Q90',#:'ec_fut_fin_better', 
                        'Q91',#:'ec_good_times',
                        'Q92',#:'ec_depression', 
                    ],

                    'spend_intentions' :[
                        'Q93',#:'ec_buy',

                        'Q95_1',# : 'spend_savings_emergencies',
                        'Q95_3',# : 'spend_necessities_bills',
                        'Q95_4',# : 'spend_entertainment_gift_loved_one',

                        'Q62', #: 'netflix_intend_to_get',
                    ],

                    'media_consumption_intensity' : [
                        'Q65',#:'track_news_daily', 
                        'Q68',#:'social_media_time', 
                        'Q69',#:'social_media_posting',
                        'Q67_0',#: 'sports_programming_0',
                        'Q67_1',#: 'sports_programming_1', 
                        'Q67_2',#: 'sports_programming_2',
                        'Q70_0',#: 'video_watching_0', 
                        'Q70_1',#: 'video_watching_1', 
                        'Q70_2',#: 'video_watching_2',

                        'Q59', #: 'netflix_frequent_viewer',
                        'Q60', #: 'netflix_binger',
                    ],    

                    'follower_characteristics' : [
                        'Q63',#:'superbowl',
                        'Q66',#:'read_reviews',
                        'Q55',#:'rec_lik_follow'
                        'Q54',#:'rec_lik_ask',
                    ],

                    'influencer_characteristics' : [
                        'Q52_1',#:'post_lik_pos', 
                        'Q52_2',#:'post_lik_neg', 
                        'Q53',#:'movie_activ_rec', 
                        'Q51',#:'entertain_freq'
                        'Q61', # : 'netflix_active_recommender',
                    ],                        

}

'''
meta_groups contains labels for the buckets of the variable groups
'''

meta_groups = [
      ('Demographics', '', 'Biological characteristics', 'demographics_biological'),
      ('Demographics', '', 'Socio-economic status', 'demographics_socio_economic'),

      ('General psychographics', '', 'Values and beliefs', 'values_and_beliefs'),
      ('General psychographics', '', 'Big 5 personalities', 'personality'),
      ('General psychographics', '', 'Regularly felt emotions', 'emotional_state'),
      ('General psychographics', '', 'Character and ethical choices', 'character_ethics'),
      ('General psychographics', '', 'Lifestyle', 'lifestyle'),

      ('Consumer psychographics', 'Products and services', 'Product preferences', 'product_preferences'),
      ('Consumer psychographics', 'Products and services', 'Online service use', 'online_service_usage'),
      ('Consumer psychographics', 'Products and services', 'Browser', 'browser'),

      ('Consumer psychographics', 'Media', 'Media choice', 'media_source'),
      ('Consumer psychographics', 'Media', 'Media consumption intensity', 'media_consumption_intensity'),
      ('Consumer psychographics', 'Media', 'Media trust', 'media_trust'),

      ('Consumer psychographics', 'Influence', 'Influencer characteristics', 'influencer_characteristics'),
      ('Consumer psychographics', 'Influence', 'Follower characteristics', 'follower_characteristics'),

      ('Consumer psychographics', 'Economics', 'Spend intentions', 'spend_intentions'),
      ('Consumer psychographics', 'Economics', 'Price sensitivity', 'price_sensitivity'),
      ('Consumer psychographics', 'Economics', 'Economic outlook', 'economic_outlook'),

      ('Consumer psychographics', 'Food', 'Food habits and attitudes', 'food_habits_and_attitudes'),
      ('Consumer psychographics', 'Food', 'Breakfast food choice', 'breakfast_food_choice'),
      ('Consumer psychographics', 'Food', 'Breakfast food choice motivations', 'breakfast_motivations'),
]

meta_groups = pd.DataFrame(meta_groups)
meta_groups.columns = ['l0', 'l1', 'l2', 'l3']

'''
CustomDataset object takes care of supplying an observation (image, labels).
It also performs image preprocessing, such as normalization by color channel. 
In case of training, it also performs random transformations, such as horizontal flips, resized crops, rotations, and color jitter -- to expand the observation pool.
'''

class CustomDataset(Dataset):

    def __init__(self, data, tr = True, cropped=False):

        self.data = data
        if not cropped:
            self.paths = self.data['img_path'].values.astype('str')
        else:
            self.paths = self.data['img_path_face_only'].values.astype('str')
        self.data_len = self.data.shape[0]

        self.labels = self.data[q_list].values.astype('int32')
        self.image_metrics = self.data[im_list].values.astype('float32')

        # transforms
        if tr:
            self.transforms = transforms.Compose([
                transforms.Resize(224),
                transforms.RandomHorizontalFlip(p=0.5),
                transforms.RandomApply([
                    transforms.RandomResizedCrop(224),
                    transforms.RandomRotation(20),
                    transforms.ColorJitter(brightness=0.1,contrast=0.1,saturation=0.1,hue=0.1)], p=0.75),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406],[0.229, 0.224, 0.225])])
        else:
            self.transforms = transforms.Compose([
                transforms.Resize(224),
                transforms.ToTensor(), 
                transforms.Normalize([0.485, 0.456, 0.406],[0.229, 0.224, 0.225])])

    def __getitem__(self, index):
        
        img_path = PATH + '/'+ self.paths[index]
        img = Image.open(img_path)
        img_tensor = self.transforms(img)
        label = self.labels[index]
        image_metric = self.image_metrics[index]

        return (img_tensor, label, image_metric)

    def __len__(self):
        return self.data_len



class Ensemble(torch.nn.Module):
    def __init__(self, modelA, modelB):
        super(Ensemble, self).__init__()
        self.modelA = modelA
        self.modelB = modelB
        
    def forward(self, x):
        x1 = self.modelA(x)
        x2 = self.modelB(x)
        out = torch.cat((x1, x2), dim=1)
        return out



# https://github.com/cydonia999/VGGFace2-pytorch/blob/master/demo.py
# https://github.com/cydonia999/VGGFace2-pytorch#pretrained-models

# module to assist with VGG loading
import models.resnet as ResNet
from models import utils

# get pretrained resnet50 models - default imagenet + VGGFace2
def get_pretrained(finetuned=False):
    
    # generic imagnet resnet
    if finetuned:
        # finetuning
        if CUDA:
            model_imgnet = torch.load(RESULTS+"/finetuned_imgnet_model")
        else:
            model_imgnet = torch.load(RESULTS+"/finetuned_imgnet_model", map_location=torch.device('cpu'))
    else:
        # no finetuning
        model_imgnet = models.resnet50(pretrained=True) # provided by torchvision
    
    # vgg2 face resnet (no finetuning)
    model_vgg = ResNet.resnet50(num_classes=8631, include_top=True)
    utils.load_state_dict(model_vgg, './models/resnet50_ft_weight.pkl')

    model_imgnet = torch.nn.Sequential(*list(model_imgnet.children())[:-1])
    model_vgg = torch.nn.Sequential(*list(model_vgg.children())[:-1])

    for param in model_imgnet.parameters():
        param.requires_grad = False

    for param in model_vgg.parameters():
        param.requires_grad = False

    model_imgnet.eval()
    model_vgg.eval()

    if CUDA:
        model_imgnet.cuda()
        model_vgg.cuda()

    model = Ensemble(model_imgnet, model_vgg)
    return model




# create an object that uses CustomDataset object from above to load multiple observations in parallel
def create_dataloader(data, rand=True, cropped=False):

    if rand: # shuffle observations
        dataset = CustomDataset(data, tr=True, cropped=cropped)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=False)
    
    else: # load observations in the original order from data
        dataset = CustomDataset(data, tr=False, cropped=cropped)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False, sampler = torch.utils.data.sampler.SequentialSampler(dataset), num_workers=0, drop_last=False)

    return loader




# finetune and save generic imagenet resnet neural net
def finetune_and_save(loader_train, loader_test, n_epochs=20):

    # loading pretrained model and preparing it for finetuning
    model = models.resnet50(pretrained=True)
    model.fc = torch.nn.Linear(model.fc.in_features, 2*len(q_list)) 
    # double the number of variables due to cross-entropy loss

    for param in model.parameters():
        param.requires_grad = True

    if CUDA:
        model.cuda()

    model.train()

    # optimize only last six layers
    layers = list(model.children())
    params = list(layers[len(layers)-1].parameters())+list(layers[len(layers)-2].parameters())+list(layers[len(layers)-3].parameters())+list(layers[len(layers)-4].parameters())+list(layers[len(layers)-5].parameters())+list(layers[len(layers)-6].parameters())
    optimizer = optim.Adamax(params=params, lr=0.001)

    hist = {}
    hist['d_labs'] = q_list

    hist['train_loss'] = []
    hist['val_loss'] = []

    # train and evaluate
    for epoch in range(n_epochs):
        
        train_loss = run_epoch(model, loss_f, optimizer, loader_train, update_model = True) # training
        eval_loss = run_epoch(model, loss_f, optimizer, loader_test, update_model = False) # evaluation
        # print('epoch: {} \ttrain loss: {:.6f} \tvalidation loss: {:.6f}'.format(epoch, train_loss, eval_loss))

        hist['train_loss'].append(train_loss)
        hist['val_loss'].append(eval_loss)

        with open(RESULTS+'/eval_record.json', 'w') as fjson:
            json.dump(hist, fjson)

    # saving model
    torch.save(model, RESULTS+"/finetuned_imgnet_model")
    return




# function that performa training (or evaluation) over an epoch (full pass through a data set)
def run_epoch(model, loss_f, optimizer, loader, update_model = False):

    if update_model:
        model.train()
    else:
        model.eval()

    loss_hist = []

    for batch_i, var in enumerate(loader):

        loss = loss_f(model, var)

        if update_model:
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        loss_hist.append(loss.data.item())

    return np.mean(loss_hist).item()




# function to compute loss from a batch data
def loss_f(model, var):
    
    data, target, _ = var
    # data [n, 3, 224, 224]
    # target [n, 349]
    # image metrics [n, 11]

    data, target = Variable(data), Variable(target)
    if CUDA:
        data, target = data.cuda(), target.cuda()
    
    output = model(data) # [n, 2*349=698]
    
    loss = 0
    loss_detailed = []
    auc_detailed = []

    for i in range(len(q_list)):
        # output contains scores for each of two levels of every predicted binary variable in q_list
        # all variables ordered as in q_list
        # (2*(i+1))-2: (2*(i+1)) then give exact coordinates of the scores for variable i
        # among all scores in the output
        ind = (2*(i+1))
        loss += F.cross_entropy( output[:,(ind-2):ind], target[:,i].long() )
    
    return loss



# extract data from a dataloader as a set of image features X and set of labels y, corresponding to those image features
# can also blackout specified areas of the loaded images before extracting the image features -- this is used in our experiments
# when data loader is deterministic, then it will load in the same data again and again
def extract_data(loader, model, blackout=None):

    X = []
    y = []
    z = []

    for batch_i, var in enumerate(loader):

        data, target, immetr = var
        
        if blackout is not None:
            data[:, :, blackout[0]:blackout[1],  blackout[2]:blackout[3]] = 0.0

        data, target, immetr = Variable(data), Variable(target), Variable(immetr)
        if CUDA:
            data, target, immetr = data.cuda(), target.cuda(), immetr.cuda()
    
        data_out = model(data)

        X.append(data_out.detach().cpu().numpy())
        y.append(target.detach().cpu().numpy())
        z.append(immetr.detach().cpu().numpy())


    X = np.vstack(X).squeeze()
    y = np.vstack(y)
    z = np.vstack(z)

    return X, y, z



# function to evaluate a set of trained classifier using AUC metric
# 'models' contains classifiers in order of binary variables to be predicted -- which are contaiend in Y
# X is a matrix of covariates
def analytics_lin(models, X, Y):
    auc = {}
    for i in range(Y.shape[1]):
        y_true = Y[:,i]
        mod = models[i]
        # auc
        y_prob = mod.predict(X)
        if np.unique(y_true).shape[0] > 1: 
            auc[q_list[i]] = metrics.roc_auc_score(y_true, y_prob)
        else:
            auc[q_list[i]] = np.NaN
    return auc


# sequentially yield coordinates for blackout in an image
def sliding_window(image_shape, stepSize, windowSize):
    # slide a window across the image
    for yc in range(0, image_shape[0], stepSize):
        for xc in range(0, image_shape[1], stepSize):
            # yield the current window
            yield (yc, yc + windowSize[1], xc, xc + windowSize[0])


# calculating decrease in AUC when blocking a particular area of an image -- over 8x8 grid placed over the image
def img_area_importance(model, models, svd, dat, auc_true):

    patch_importance = {}

    for (y0, y1, x0, x1) in sliding_window(image_shape=(224,224), stepSize = 28, windowSize=(28,28)):

        loader = create_dataloader(dat,rand=False)

        # X_modified_raw contains image features extracted from images with a portion of the image blocked
        X_modified_raw, Y, _ = extract_data(loader, model, (y0, y1, x0, x1))

        # image features reduced to 500 via svd
        X_modified = svd.transform(X_modified_raw)

        auc = analytics_lin(models, X_modified, Y)

        patch_importance_q = {} # contains -(decrease in auc after blocking of an image)
        
        for q in q_list:
            patch_importance_q[q] = auc_true[q] - auc[q]

        patch_importance[(y0, y1, x0, x1)] = patch_importance_q # decrease in auc across all variables -- for the given blocked portion of the image

    return patch_importance




# START OF THE RUN

torch.set_num_threads(1)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

CUDA = torch.cuda.is_available()

PATH = './data'
RESULTS = './results'

batch_size = 10

os.makedirs(RESULTS, exist_ok=True)


#finetune model just by running this script
data = pd.read_csv(PATH+'/data.csv')

# data summary stats

# data size
data.shape # observations
data['randomID'].unique().shape # users

data[data['source']==1].shape # observations - qualtrics
data['randomID'][data['source']==1].unique().shape # users - qualtrics

data[data['source']==0].shape # observations - mturk
data['randomID'][data['source']==0].unique().shape # users - mturk


# female Q11_1 stats by data source 
data['Q11_1'].mean() 
data['Q11_1'][data['source']==1].mean() # qualtrics
data['Q11_1'][data['source']==0].mean() # mturk


# Generating a set of useful global constants

# sorted list of variables
q_list = sorted(list(q_to_name_dict.keys()))

q_to_d_dict = {} # number of levels per variable (portion of code were originally written to support multinomial, not only binary vars)
random_threshold = {} # random guess threshold
prop = {} # proportion of class 1 in the data (vs. 0)
for i in q_list:
    q_to_d_dict[i] = np.unique(data[i]).shape[0]
    random_threshold[i] = 1.0/q_to_d_dict[i]
    prop[i] = data[i].sum()/data.shape[0]

# image metrics
im_list = sorted(list(image_metrics.keys()))


# https://stats.stackexchange.com/questions/328614/estimation-of-bayesian-ridge-regression
# Bayesian ridge regresssion - linear probability model
def ridge_regression(X, y):
    return BayesianRidge(n_iter=int(1e7), tol=1e-6, normalize=False).fit(X, y)


# train many regressions
def train_eval_regressions(Xtr, Ytr, Xts, Yts):
    lin_models = []
    for i in range(len(q_list)): #tqdm
        clf = ridge_regression(Xtr, Ytr[:,i])
        lin_models.append(clf)
    auc = analytics_lin(lin_models, Xts, Yts)
    return auc, lin_models



# CODING INDIVIDUALS INTO GROUPS BY DEMOGRAPHICS

# 'Q11_0': 'Gender: Male', 'Q11_1':'Gender: Female', 'Q11_2':'Gender: Other',
# 'Q12_0': 'Age: <=30', 'Q12_1': 'Age: (30; 50] ', 'Q12_2': 'Age: > 50',
# 'Q13_0': 'Race: Caucasian/ White', 'Q13_1': 'Race: Asian','Q13_2': 'Race: Hispanic/ Latino','Q13_3': 'Race: African American/ Black','Q13_4': 'Race: Other',

demographic_vars = ['Q11_1','Q11_2','Q12_1','Q12_2','Q13_1','Q13_2','Q13_3','Q13_4']
dem_ref = data[demographic_vars].drop_duplicates(subset=demographic_vars)
d = {}

for j in range(dem_ref.shape[0]):
    d[j] = 0
    for i in range(data.shape[0]):
        d[j]+= 1*(data[demographic_vars].iloc[i] == dem_ref.iloc[j]).all()

inds = []
for i in d.keys():
    if d[i] >= 25:
        inds.append(i)

# percent of observations contained in the target demographic groups
sum([d[i] for i in inds])/data.shape[0]

# reference group "other"
dem_ref['demographic_code'] = 0

for i in range(len(inds)):
    dem_ref['demographic_code'].iloc[inds[i]]=i+1

dem_ref = pd.get_dummies(dem_ref, prefix='dem', drop_first=True, columns=['demographic_code']).reset_index(drop=True)

dem_code_var = dem_ref.columns[len(demographic_vars):].tolist()



# TRAINING

np.random.seed(999)
torch.manual_seed(999)

results_auc = []
results_patch_importance = []
results_auc_cropped = []
results_auc_demographics = []
results_auc_shallowfacemetrics = []
results_auc_demographics_shallowfacemetrics = []
results_auc_all_plus_img = []
results_auc_all_plus_img_cropped = []

# individual IDs
IDs = data['randomID'].unique()

# random shuffle split generator
# This is referred to as repeated training-test split, or leave-group-out cross-validation, or Monte Carlo cross-validation. 
# See Applied Predictive Modeling by Kuhn and Johnson, Springer, 2013.
# rs = ShuffleSplit(n_splits=5, test_size=0.2, random_state=999)

n_reps = 20 # number of repeats for 5-fold cross-valaidtion
gkf = KFold(n_splits=5)

for rep in tqdm(range(n_reps)):

    # shuffling every repetition to get new folds via cv procedure
    np.random.shuffle(IDs)
    data_shuffled = data.sample(frac=1.0) # shufling observations too

    #train_index, test_index = next(enumerate(rs.split(IDs)))[1]
    for train_index, test_index in tqdm(gkf.split(IDs)):

        # train and test user IDs
        trainID = IDs[train_index]
        testID = IDs[test_index]

        # extracting split data
        data_train = data_shuffled[data_shuffled['randomID'].isin(trainID)]
        data_test = data_shuffled[data_shuffled['randomID'].isin(testID)]

        # creating data loaders
        loader_train = create_dataloader(data_train,rand=False)
        loader_train_rand = create_dataloader(data_train,rand=True) # to finetune neural net
        loader_test = create_dataloader(data_test,rand=False)

        # finetuning imgnet
        finetune_and_save(loader_train_rand, loader_test)

        # loading a neural net ensemble
        model = get_pretrained(finetuned=True)

        # extracting image features, labels, and ratios calculated from images (used as control)
        X_train_raw, Y_train, Z_train = extract_data(loader_train, model)
        X_test_raw, Y_test, Z_test = extract_data(loader_test, model)

        # reducing number of features
        svd = TruncatedSVD(n_components=500, random_state=0, n_iter=100).fit(X_train_raw)
        X_train = svd.transform(X_train_raw)
        X_test = svd.transform(X_test_raw)

        # creating data loaders - CROPPED
        loader_train_cropped = create_dataloader(data_train,rand=False,cropped=True)
        loader_test_cropped = create_dataloader(data_test,rand=False,cropped=True)

        # extracting image features and labels
        X_train_raw_cropped, _, _ = extract_data(loader_train_cropped, model)
        X_test_raw_cropped, _, _ = extract_data(loader_test_cropped, model)

        # reducing number of features
        svd_cropped = TruncatedSVD(n_components=500, random_state=0, n_iter=100).fit(X_train_raw_cropped)
        X_train_cropped = svd_cropped.transform(X_train_raw_cropped)
        X_test_cropped = svd_cropped.transform(X_test_raw_cropped)

        # demographic predictive groups
        Y_train_df = pd.DataFrame(Y_train, columns=q_list)
        Y_test_df = pd.DataFrame(Y_test, columns=q_list)

        Y_train_demographics = Y_train_df[demographic_vars]
        Y_test_demographics = Y_test_df[demographic_vars]

        Y_train_demographics = pd.merge(Y_train_demographics,dem_ref,on=demographic_vars,sort=False,how='left')
        Y_test_demographics = pd.merge(Y_test_demographics,dem_ref,on=demographic_vars,sort=False,how='left')

        Y_train_demographics = Y_train_demographics.values
        Y_test_demographics = Y_test_demographics.values


        # TRAINING

        # deep image features
        auc, lin_models = train_eval_regressions(X_train, Y_train, X_test, Y_test)
        results_auc.append(auc)

        # heat maps - image area importance 
        patch_importance = img_area_importance(model, lin_models, svd, data_test, auc)
        results_patch_importance.append(patch_importance)

        # deep image features CROPPED
        auc, lin_models = train_eval_regressions(X_train_cropped, Y_train, X_test_cropped, Y_test)
        results_auc_cropped.append(auc)


        # demographics
        auc, lin_models = train_eval_regressions(Y_train_demographics, Y_train, Y_test_demographics, Y_test)
        results_auc_demographics.append(auc) 

        # manual (shallow) facial metrics
        auc, lin_models = train_eval_regressions(Z_train, Y_train, Z_test, Y_test)
        results_auc_shallowfacemetrics.append(auc)    


        # demographics + manual facial metrics
        auc, lin_models = train_eval_regressions(np.concatenate([Y_train_demographics, Z_train],1), Y_train, 
            np.concatenate([Y_test_demographics, Z_test],1), Y_test)
        results_auc_demographics_shallowfacemetrics.append(auc)


        # demographics + manual facial metrics + deep image features
        auc, lin_models = train_eval_regressions(np.concatenate([X_train, Y_train_demographics, Z_train],1), Y_train, 
            np.concatenate([X_test, Y_test_demographics, Z_test],1), Y_test)
        results_auc_all_plus_img.append(auc)

        auc, lin_models = train_eval_regressions(np.concatenate([X_train_cropped, Y_train_demographics, Z_train],1), Y_train, 
            np.concatenate([X_test_cropped, Y_test_demographics, Z_test],1), Y_test)
        results_auc_all_plus_img_cropped.append(auc)


# saving results

pd.DataFrame(results_auc).to_csv(RESULTS+'/crossvalidation_auc.csv', index=False)
pd.DataFrame(results_auc_cropped).to_csv(RESULTS+'/crossvalidation_auc_cropped.csv', index=False)
pd.DataFrame(results_auc_demographics).to_csv(RESULTS+'/crossvalidation_auc_demographics.csv', index=False)
pd.DataFrame(results_auc_shallowfacemetrics).to_csv(RESULTS+'/crossvalidation_auc_shallowfacemetrics.csv', index=False)
pd.DataFrame(results_auc_demographics_shallowfacemetrics).to_csv(RESULTS+'/crossvalidation_auc_demographics_shallowfacemetrics.csv', index=False)
pd.DataFrame(results_auc_all_plus_img).to_csv(RESULTS+'/crossvalidation_auc_all_plus_img.csv', index=False)
pd.DataFrame(results_auc_all_plus_img_cropped).to_csv(RESULTS+'/crossvalidation_auc_all_plus_img_cropped.csv', index=False)


# saving patch_importance
patch_importance = {}
for q in q_list:

    arr = np.zeros((224,224))
    
    for (y0, y1, x0, x1) in sliding_window(image_shape=(224,224), stepSize = 28, windowSize=(28,28)):
        arr[y0:y1, x0:x1] = np.mean([i[(y0, y1, x0, x1)][q] for i in results_patch_importance])

    patch_importance[q] = arr.tolist()


with open(RESULTS+'/patch_importance.json', 'w') as fjson:
    json.dump(patch_importance, fjson)






# VISUALIZATIONS
colors = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', 
    '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabebe', 
    '#469990', '#e6beff', '#9A6324', '#fffac8', '#800000', 
    '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#ffffff', '#000000']


# extracting auc data for each fold of crossvalidation (cv) and each variable
results_auc = pd.read_csv(RESULTS+'/crossvalidation_auc.csv')

# checking normality of AUC distribution using Shapiro-Wilk test
h0_normal = np.array([scipy.stats.shapiro(results_auc[x].dropna())[1] for x in results_auc.columns])>0.05
sum(h0_normal)/h0_normal.shape[0] # 91% of variables

results_auc = results_auc.stack().reset_index()
results_auc.columns = ['cv_fold', 'var_name', 'auc']

results_auc['var_name_full'] = [q_to_full_name_dict[i] for i in results_auc['var_name']]

# calculating mean AUC mean and sd across cv folds for each variable
results_auc = results_auc[['var_name_full','var_name', 'auc']].groupby(['var_name_full','var_name'],sort=False).agg(['mean','std']).reset_index()
results_auc.columns = results_auc.columns.map('_'.join).str.strip('_')

# calculating confidence interval on auc for each variables
results_auc['auc_l'] = results_auc['auc_mean'] - 2*results_auc['auc_std']
results_auc['auc_u'] = results_auc['auc_mean'] + 2*results_auc['auc_std']

# mean value of the variable in the full data
temp = data[q_list].mean().reset_index()
temp.columns = ['index', 'var_mean']
results_auc = results_auc.merge(temp, left_on='var_name', right_on='index')
results_auc = results_auc.drop('index',axis=1)

# p values
results_auc['p_val'] = [scipy.stats.norm(results_auc['auc_mean'].iloc[i], results_auc['auc_std'].iloc[i]).cdf(0.5) for i in range(results_auc.shape[0])]
results_auc['p_val'] = results_auc['p_val'].fillna(0.0) # for variables predicted perfectly with variance 0 - clearly, significantly predicted

# save auc analysis
results_auc.to_csv(RESULTS+'/results_auc.csv')




# analysis by group
results_auc_g = results_auc.copy()
results_auc_g['group_name'] = np.nan

for gr in var_groups.keys():
    ind = results_auc_g['var_name'].isin(var_groups[gr])
    results_auc_g.loc[ind,'group_name'] = gr

# drop variables without specified groups (e.g., data source)
results_auc_g = results_auc_g.dropna()

# merge with nice group names
results_auc_g = meta_groups.merge(results_auc_g, how='right', left_on='l3', right_on='group_name', sort=False)
results_auc_g_full = results_auc_g.copy()

# calculating percentiles by variable group
results_auc_g = results_auc_g[['l0', 'l2', 'group_name', 'auc_mean', 'auc_l', 'auc_u']].groupby(['l0', 'l2', 'group_name'],sort=False).mean().reset_index() 

results_auc_g.to_csv(RESULTS+'/results_auc_by_group.csv')

results_auc_g = results_auc_g.sort_values('auc_mean', ascending=False)




# GROUP MEANS

# Func to draw line segment
def newline(p1, p2, linewidth =1.0, color='firebrick'):
    ax = plt.gca()
    l = mlines.Line2D([p1[0],p2[0]], [p1[1],p2[1]], linewidth = linewidth, color=color)
    ax.add_line(l)
    return l


# plot group results as group chart with error bars
plt.figure(figsize=(6,8), dpi=300)

# sets vertical index
plt.hlines(y=results_auc_g['l2'].tolist(), xmin=0, xmax=1, color='gray', alpha=0.0, linewidth=.5, linestyles='dashdot')

# plots dots
plt.scatter(results_auc_g_full['auc_mean'].values, results_auc_g_full['l2'].tolist(), marker='o', s = 75., edgecolors='gray', c='w', alpha=0.3)
plt.scatter(results_auc_g['auc_mean'].values, results_auc_g['l2'].tolist(), marker='o', s = 75., color='firebrick')

plt.axvline(x=0.5, color='k', linestyle=':')

plt.xlim([0.4,1])
plt.xlabel('AUC')
plt.gca().invert_yaxis()

#plt.gca().xaxis.grid(True, alpha=.4, linewidth=.1)
#plt.legend(loc='center right')

gray_patch = plt.plot([],[], marker="o", ms=10, ls="", markerfacecolor='w', markeredgecolor='gray', label="Variable AUC", alpha=0.3)
red_patch = plt.plot([],[], marker="o", ms=10, ls="", color='firebrick', label="Group mean AUC")
leg = plt.legend(handles=[gray_patch[0], red_patch[0]], loc='lower right', bbox_to_anchor=(1., -0.15), ncol=2, fontsize=11.)


plt.gca().spines["top"].set_visible(False)    
plt.gca().spines["bottom"].set_visible(False)    
plt.gca().spines["right"].set_visible(False)    
plt.gca().spines["left"].set_visible(False)   

plt.grid(axis='both', alpha=.4, linewidth=.1)

plt.savefig(RESULTS+'/group_auc.pdf', bbox_inches='tight', transparent=True)
plt.close()



# INDIVIDUAL VARIABLE MEANS
results_auc = results_auc.sort_values('p_val', ascending=True)
results_auc_filtered = results_auc[results_auc['auc_l']>0.5]

# number of variables with significant AUC
results_auc_filtered.shape[0]

# % variables with significant AUC 
results_auc_filtered.shape[0]/results_auc.shape[0]



# FALSE DISCOVERY RATE UNDER ARBITRARY DEPENDENCE

alpha = 0.05 # desired control level for FDR

plt.figure(figsize=(10,10))
plt.scatter(list(range(results_auc['p_val'].shape[0])), results_auc['p_val'], color='black')
axes = plt.gca()
x_vals = np.array(axes.get_xlim())
slope = alpha/results_auc.shape[0] 
y_vals = slope * x_vals
bhline, = plt.plot(x_vals, y_vals, '--', color='red')
plt.xlabel('k')
plt.ylabel('p-value')
plt.savefig(RESULTS+'/fdr.pdf', bbox_inches='tight', transparent=True)
plt.close()


# FDRc under Empirical Bayes view
below = results_auc['p_val'].values <= slope * np.array(list(range(1,1+results_auc['p_val'].shape[0])))
max_below = np.max(np.where(below)[0])
pth = results_auc['p_val'].values[max_below]
print('Threshold p_i:', pth) # 0.00699
results_auc[results_auc['p_val']<=pth]
results_auc[results_auc['p_val']<=pth].shape[0]
tot_fdr = max_below + 1

# confirmed results match those in
# from statsmodels.stats.multitest import multipletests
# multipletests(results_auc['p_val'].values, alpha=0.05, method='fdr_bh', is_sorted=False, returnsorted=False)[0]



# import seaborn as sns
df = data[q_list].copy()

# correlation matrix
Xcorr = df.corr().values

# distances based on sign-less correlation matrix
d = sch.distance.squareform(1-np.abs(Xcorr))

# hierarchical clustering linkage
L = sch.linkage(d, method='single')

sns_plot = sns.clustermap(Xcorr, figsize=(40, 40), row_linkage=L, col_linkage=L, xticklabels=25, yticklabels=25, linewidths=0, rasterized=True)

ax = sns_plot.ax_heatmap

cols = [df.columns[i] for i in list(sns_plot.data2d.columns)]
vl = [cols.index(q) for q in results_auc_filtered['var_name'].values[:tot_fdr]]
vl1 = [cols.index(q) for q in results_auc_filtered['var_name'].values[tot_fdr:]]

for v in vl: 
    ax.axvline(x=v+0.5, ymin=0, ymax=(sns_plot.data2d.shape[1]-v-0.5)/sns_plot.data2d.shape[1], color='#42d4f4', linewidth=2)

ax.set_xticklabels(list(range(0,len(cols),25)), fontsize = 20) #ax.get_xmajorticklabels()
ax.set_yticklabels(list(range(0,len(cols),25)), fontsize = 20)

sns_plot.fig.axes[-1].tick_params(labelsize=25)

sns_plot.savefig(RESULTS+'/var_corr1.pdf')
plt.close()


# saving ordered data
temp = pd.DataFrame.from_dict({'Variable':[q_to_full_name_dict[i] for i in cols],
        'Question': cols}).reset_index().merge(results_auc.reset_index(drop=True),
        how='left', left_on = 'Question', right_on='var_name')
temp.loc[:,['auc_mean', 'auc_std', 'auc_l', 'auc_u', 'var_mean']] = temp[['auc_mean', 'auc_std', 'auc_l', 'auc_u', 'var_mean']].round(2)
temp.loc[:,'p_val'] = temp.loc[:,'p_val'].round(4)
temp.to_csv(RESULTS+'/var_corr1_order.csv',index=False)


temp = pd.DataFrame.from_dict({'Variable':[q_to_full_name_dict[i] for i in cols],
        'Question': cols}).reset_index().merge(results_auc.reset_index(drop=True),
        how='left', left_on = 'Question', right_on='var_name')
temp.loc[:,['auc_mean', 'auc_std', 'auc_l', 'auc_u', 'var_mean']] = temp[['auc_mean', 'auc_std', 'auc_l', 'auc_u', 'var_mean']].round(2)
temp = temp.sort_values(['p_val'], ascending=[True]).reset_index(drop=True)
temp.loc[:,'p_val'] = temp.loc[:,'p_val'].round(4)
temp.to_csv(RESULTS+'/var_pval_order.csv',index=False)



# body fitness (Q21) and iPhone Safari browser (Q6_1_TEXT_0) dependence # remove Q6_1_TEXT_1

import statsmodels.api as sm

# correlation matrix with clustered standard errors
def correlate_clustered(X, clusters):

    X_norm = ( X-X.mean() ) / X.std() # normalization
    k = X_norm.shape[1]
    corr = np.eye(k)
    corr_pval = np.zeros((k,k))
    for i in range(k):
        for j in range(k):
            if i != j:
                mod = sm.OLS(X_norm.iloc[:,i], X_norm.iloc[:,j], missing='drop')
                res = mod.fit(cov_type = "cluster", cov_kwds = {"groups":clusters.tolist()}) 
                corr[i,j] = res.params[0]
                corr_pval[i,j] = res.pvalues[0]

    corr = pd.DataFrame(corr, columns=X_norm.columns, index=X_norm.columns)
    corr_pval = pd.DataFrame(corr_pval, columns=X_norm.columns, index=X_norm.columns)
    return corr, corr_pval


temp = results_auc.iloc[:30]
temp.index = temp['var_name']

# temp1 = data[temp.index.tolist()]
# temp1.columns = temp['var_name_full'].tolist()
# rho = temp1.corr()
# rho[['Body fitness','Browser: Safari iPhone']].to_csv(RESULTS+'/body_fitness.csv')

# individual-clustered standard errors for correlation coefficient

X = data[temp.index.tolist()].copy()
X.columns = temp['var_name_full'].tolist()
clusters = data['randomID']

corr, corr_pval = correlate_clustered(X, clusters)

corr[['Body fitness','Browser: Safari iPhone']].to_csv(RESULTS+'/body_fitness.csv')
corr_pval[['Body fitness','Browser: Safari iPhone']].to_csv(RESULTS+'/body_fitness_pval.csv')
corr_sig = corr_pval[['Body fitness','Browser: Safari iPhone']]<=0.01
corr_sig.to_csv(RESULTS+'/body_fitness_sign.csv')

# all coef values above this threshold are significant (>= 0.085)
corr[['Body fitness','Browser: Safari iPhone']][~corr_sig].abs().max()

# all coef values below this threshold are insignificant (<= 0.08)
corr[['Body fitness','Browser: Safari iPhone']][corr_sig].abs().min()





# PCA ANALYSIS
pca = PCA().fit(data[q_list])

# scree plot
plt.figure(figsize=(10, 10))
plt.plot(np.cumsum(pca.explained_variance_ratio_))
plt.xlabel('Number of components')
plt.ylabel('Cumulative explained variance')
plt.savefig(RESULTS+'/pca_scree.pdf', bbox_inches='tight', transparent=True)
plt.close()

# min number of factors that explain 50% of variance -- 47
sum(np.cumsum(pca.explained_variance_ratio_)<0.5)+1

# top 12 pcs
np.cumsum(pca.explained_variance_ratio_)[11]

# number of eigenvalues > 1
sum(pca.explained_variance_ >1)

# percent of variance explained by factors with eigenvalue>1
np.cumsum(pca.explained_variance_ratio_)[:sum(pca.explained_variance_ >1)][-1]

# top and bottom loading variabels on top 6 factors
[q_to_full_name_dict[q_list[j]] for j in np.argmax(pca.components_.T,0)[:6].tolist()]
[q_to_full_name_dict[q_list[j]] for j in np.argmax(-pca.components_.T,0)[:6].tolist()]

# looking at factor loadings
loadings = pca.components_.T * np.sqrt(pca.explained_variance_)
first_tot = np.unique(np.argmax(loadings, axis=1))

ind = [(q in results_auc_filtered['var_name'].tolist()) for q in q_list]
first_sig = np.unique(np.argmax(loadings[ind], axis=1))

two_sig = np.unique(np.argsort(-loadings[ind], axis=1)[:,:2])

# some conservative ratios to control false positive rate via number of most important factors
# among significantly predicted variables
first_sig.shape[0]/len(q_list)
first_sig.shape[0]/first_tot.shape[0]
first_sig.shape[0]/next(x[0] for x in enumerate(np.cumsum(pca.explained_variance_ratio_)) if x[1] > 0.8)

two_sig.shape[0]/len(q_list)


# varimax rotation - top 12 components - only 27% of variance explained - np.cumsum(pca.explained_variance_ratio_)[11]
fa = FactorAnalysis(12, svd_method='lapack', rotation='varimax', max_iter=10000, random_state=999).fit(data[q_list])
# fa.components_ # (components, features)
# tvmax = np.array(q_list)[np.unique(np.argmax(fa.components_, axis=1))]
# tvmin = np.array(q_list)[np.unique(np.argmax(-fa.components_, axis=1))]
# [q_to_full_name_dict[i] for i in tvmax]
# [q_to_full_name_dict[i] for i in tvmin]

pd.DataFrame(fa.components_.T, index= [q_to_full_name_dict[i] for i in q_list]).to_csv(RESULTS+'/factor_loadings_varimax.csv')



# INDIVIDUAL VARIABLES - PART 1

# plot group results as group chart with error bars
plt.figure(figsize=(6,20), dpi=300)

# sets vertical index
plt.hlines(y=results_auc_filtered['var_name_full'].tolist()[:tot_fdr], xmin=0, xmax=1, color='gray', alpha=0.0, linewidth=.5, linestyles='dashdot')

# plots dots
plt.scatter(results_auc_filtered['auc_mean'].values[:tot_fdr], results_auc_filtered['var_name_full'].tolist()[:tot_fdr], marker='o', s = 75., color='firebrick')

# line segments
for i, p1, p2 in zip(results_auc_filtered['var_name_full'][:tot_fdr], 
    results_auc_filtered['auc_l'].values[:tot_fdr], 
    results_auc_filtered['auc_u'].values[:tot_fdr]):
    newline([p1, i], [p2, i])

plt.axvline(x=0.5, color='k', linestyle=':')

plt.xlim([0.4,1])
plt.xlabel('AUC')
plt.gca().invert_yaxis()

#plt.gca().xaxis.grid(True, alpha=.4, linewidth=.1)
#plt.legend(loc='center right')

red_patch = plt.plot([],[], marker="o", ms=10, ls="", mec=None, color='firebrick', label="AUC")
red_line = mlines.Line2D([0], [0], linewidth = 1.0, color='firebrick', label="[AUC-2SE : AUC+2SE]")
leg = plt.legend(handles=[red_patch[0], red_line], loc='lower right', bbox_to_anchor=(1., -0.07), ncol=2, fontsize=11.)

plt.gca().spines["top"].set_visible(False)    
plt.gca().spines["bottom"].set_visible(False)    
plt.gca().spines["right"].set_visible(False)    
plt.gca().spines["left"].set_visible(False)   

plt.grid(axis='both', alpha=.4, linewidth=.1)

plt.savefig(RESULTS+'/variable_auc.pdf', bbox_inches='tight', transparent=True)
plt.close()



# INDIVIDUAL VARIABLES - PART 2
# plot group results as group chart with error bars
plt.figure(figsize=(6,20), dpi=300)

# sets vertical index
plt.hlines(y=results_auc_filtered['var_name_full'].tolist()[tot_fdr:], xmin=0, xmax=1, color='gray', alpha=0.0, linewidth=.5, linestyles='dashdot')

# plots dots
plt.scatter(results_auc_filtered['auc_mean'].values[tot_fdr:], results_auc_filtered['var_name_full'].tolist()[tot_fdr:], marker='o', s = 75., color='firebrick')

# line segments
for i, p1, p2 in zip(results_auc_filtered['var_name_full'][tot_fdr:], 
    results_auc_filtered['auc_l'].values[tot_fdr:], 
    results_auc_filtered['auc_u'].values[tot_fdr:]):
    newline([p1, i], [p2, i])

plt.axvline(x=0.5, color='k', linestyle=':')

plt.xlim([0.4,1])
plt.xlabel('AUC')
plt.gca().invert_yaxis()

#plt.gca().xaxis.grid(True, alpha=.4, linewidth=.1)
#plt.legend(loc='center right')

red_patch = plt.plot([],[], marker="o", ms=10, ls="", mec=None, color='firebrick', label="AUC")
red_line = mlines.Line2D([0], [0], linewidth = 1.0, color='firebrick', label="[AUC-2SE : AUC+2SE]")
leg = plt.legend(handles=[red_patch[0], red_line], loc='lower right', bbox_to_anchor=(1., -0.07), ncol=2, fontsize=11.)

plt.gca().spines["top"].set_visible(False)    
plt.gca().spines["bottom"].set_visible(False)    
plt.gca().spines["right"].set_visible(False)    
plt.gca().spines["left"].set_visible(False)   

plt.grid(axis='both', alpha=.4, linewidth=.1)

plt.savefig(RESULTS+'/variable_auc_2.pdf', bbox_inches='tight', transparent=True)
plt.close()



# BENCHMARK PLOT

def benchmark(ref, target, saved):

    # t-test
    results_r = pd.read_csv(ref)
    results_t = pd.read_csv(target)

    colnames = results_r.columns

    ttest_res = {}
    for i in colnames:
        s, p = ttest_ind(results_r[i], results_t[i], equal_var=False, nan_policy='omit', alternative='less') # m(a) < m(b)
        ttest_res[i] = p

    ttest_res = pd.DataFrame([ttest_res]).T.reset_index()
    ttest_res.columns = ['var_name', 'ttest_less_pval']
    ttest_res['significance_ttest_less'] = 1.0 * (ttest_res['ttest_less_pval'] < 0.05)

    # reference model

    # extracting auc data for each fold of crossvalidation (cv) and each variable
    results_reference = pd.read_csv(ref)
    results_reference = results_reference.stack().reset_index()
    results_reference.columns = ['cv_fold', 'var_name', 'auc']

    # calculating mean AUC mean and sd across cv folds for each variable
    results_reference = results_reference[['var_name', 'auc']].groupby(['var_name'],sort=False).agg(['mean','std']).reset_index()
    results_reference.columns = results_reference.columns.map('_'.join).str.strip('_')

    # calculating confidence interval on auc for each variables
    results_reference['auc_l'] = results_reference['auc_mean'] - 2*results_reference['auc_std']
    results_reference['auc_u'] = results_reference['auc_mean'] + 2*results_reference['auc_std']

    # p values
    results_reference['p_val'] = [scipy.stats.norm(results_reference['auc_mean'].iloc[i], results_reference['auc_std'].iloc[i]).cdf(0.5) for i in range(results_reference.shape[0])]
    results_reference['p_val'] = results_reference['p_val'].fillna(0.0)

    results_reference = results_reference.sort_values('p_val', ascending=True)

    # significance 2SE
    results_reference['significance_2se'] = 1*(results_reference['auc_l'] > 0.5)

    # significance FDR (REQUIRES THAT p-values are sorted in ascending order)
    alpha = 0.05 # desired control level for FDR
    slope = alpha/results_reference.shape[0]

    below = results_reference['p_val'].values <= slope * np.array(list(range(1,1+results_reference['p_val'].shape[0])))
    results_reference['significance_fdr'] = 1*below


    # reference + extra features model
    results_target = pd.read_csv(target)
    results_target = results_target.stack().reset_index()
    results_target.columns = ['cv_fold', 'var_name', 'auc']

    # calculating mean AUC mean and sd across cv folds for each variable
    results_target = results_target[['var_name', 'auc']].groupby(['var_name'],sort=False).agg(['mean','std']).reset_index()
    results_target.columns = results_target.columns.map('_'.join).str.strip('_')

    # calculating confidence interval on auc for each variables
    results_target['auc_l'] = results_target['auc_mean'] - 2*results_target['auc_std']
    results_target['auc_u'] = results_target['auc_mean'] + 2*results_target['auc_std']

    # p values
    results_target['p_val'] = [scipy.stats.norm(results_target['auc_mean'].iloc[i], results_target['auc_std'].iloc[i]).cdf(0.5) for i in range(results_target.shape[0])]
    results_target['p_val'] = results_target['p_val'].fillna(0.0)

    results_target = results_target.sort_values('p_val', ascending=True)

    # significance 2SE
    results_target['significance_2se'] = 1*(results_target['auc_l'] > 0.5)

    # significance FDR  (REQUIRES THAT p-values are sorted in ascending order)
    alpha = 0.05 # desired control level for FDR
    slope = alpha/results_target.shape[0]

    below = results_target['p_val'].values < slope * np.array(list(range(1,1+results_target['p_val'].shape[0])))
    results_target['significance_fdr'] = 1*below


    # merging
    results_reference = results_reference.merge(results_target, how='outer', on='var_name', sort=False)
    results_reference['improvement'] = (results_reference['auc_mean_y']/results_reference['auc_mean_x']-1)
    results_reference = results_reference.sort_values('improvement', ascending=False)

    results_reference['var_name_full'] = [q_to_full_name_dict[i] for i in results_reference['var_name']]

    #results_reference = results_reference[results_reference['auc_l_y']>0.5]

    results_reference['significance_2se_incr'] = results_reference['significance_2se_y'] > results_reference['significance_2se_x']
    results_reference['significance_fdr_incr'] = results_reference['significance_fdr_y'] > results_reference['significance_fdr_x']

    results_reference = results_reference.merge(ttest_res, how='outer', on='var_name', sort=False)

    results_reference[['var_name_full', 'improvement', 'auc_mean_x', 'auc_mean_y', 'p_val_x', 'p_val_y', 'significance_2se_x', 'significance_2se_y', 'significance_fdr_x', 'significance_fdr_y', 'significance_2se_incr', 'significance_fdr_incr', 'ttest_less_pval', 'significance_ttest_less']].to_csv(saved+'.csv',index=False)


    k=25
    # Visualizing improvement on demographics
    plt.figure(figsize=(6,10), dpi=300)

    # plots dots
    plt.scatter(results_reference['improvement'].values[:k], results_reference['var_name_full'].tolist()[:k], marker='o', s = 75., color='firebrick')
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter())

    plt.rc('text', usetex=True)
    for a0, a1, c, v in zip(results_reference['auc_mean_x'].values[:k],results_reference['auc_mean_y'].values[:k], results_reference['improvement'].values[:k], results_reference['var_name_full'].tolist()[:k], ):
        plt.text(c+1, v, r'{} $\rightarrow$ {}'.format(round(a0,2),round(a1,2)), horizontalalignment='left', verticalalignment='center', fontdict={'size':10})
    plt.rc('text', usetex=False)

    #plt.xlim([0.,30])
    plt.xlabel('Percent improvement in AUC')
    plt.gca().invert_yaxis()

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)   

    plt.grid(axis='both', alpha=.4, linewidth=.1)

    plt.savefig(saved+'.pdf', bbox_inches='tight', transparent=True)
    plt.close()




benchmark(ref=RESULTS+'/crossvalidation_auc_demographics.csv', 
        target=RESULTS+'/crossvalidation_auc_demographics_shallowfacemetrics.csv', 
        saved=RESULTS+'/improvement_d_df')

benchmark(ref=RESULTS+'/crossvalidation_auc_demographics_shallowfacemetrics.csv', 
        target=RESULTS+'/crossvalidation_auc_all_plus_img.csv', 
        saved=RESULTS+'/improvement_df_all')

benchmark(ref=RESULTS+'/crossvalidation_auc_demographics_shallowfacemetrics.csv', 
        target=RESULTS+'/crossvalidation_auc_all_plus_img_cropped.csv', 
        saved=RESULTS+'/improvement_df_all_cropped')

benchmark(ref=RESULTS+'/crossvalidation_auc_all_plus_img_cropped.csv', 
        target=RESULTS+'/crossvalidation_auc_all_plus_img.csv', 
        saved=RESULTS+'/improvement_allcropped_all')

benchmark(ref=RESULTS+'/crossvalidation_auc_demographics.csv', 
        target=RESULTS+'/crossvalidation_auc.csv', 
        saved=RESULTS+'/improvement_d_deep')

benchmark(ref=RESULTS+'/crossvalidation_auc_demographics.csv', 
        target=RESULTS+'/crossvalidation_auc_cropped.csv', 
        saved=RESULTS+'/improvement_d_deep_cropped')

benchmark(ref=RESULTS+'/crossvalidation_auc_demographics.csv', 
        target=RESULTS+'/crossvalidation_auc_all_plus_img.csv', 
        saved=RESULTS+'/improvement_d_all')

benchmark(ref=RESULTS+'/crossvalidation_auc_cropped.csv', 
        target=RESULTS+'/crossvalidation_auc.csv', 
        saved=RESULTS+'/improvement_deepcropped_deep')


# number of significantly predictable variables by model
def waterfall(paths, model_names, saved):

    res = []

    for p in paths:

        temp = pd.read_csv(p)
        temp = temp.stack().reset_index()
        temp.columns = ['cv_fold', 'var_name', 'auc']

        # calculating mean AUC mean and sd across cv folds for each variable
        temp = temp[['var_name', 'auc']].groupby(['var_name'],sort=False).agg(['mean','std']).reset_index()
        temp.columns = temp.columns.map('_'.join).str.strip('_')

        # calculating confidence interval on auc for each variables
        temp['auc_l'] = temp['auc_mean'] - 2*temp['auc_std']
        temp['auc_u'] = temp['auc_mean'] + 2*temp['auc_std']

        temp['group_name'] = np.nan
        for gr in var_groups.keys():
            ind = temp['var_name'].isin(var_groups[gr])
            temp.loc[ind,'group_name'] = gr

        temp['p_val'] = [scipy.stats.norm(temp['auc_mean'].iloc[i], temp['auc_std'].iloc[i]).cdf(0.5) for i in range(temp.shape[0])]
        temp['p_val'] = temp['p_val'].fillna(0.0)

        temp = temp.sort_values('p_val', ascending=True)

        res.append(temp)

    predictable_n = []
    predictable_n_fdr = []

    for i in range(len(res)):

        # number of predictable variables by 2 se criterion
        t = res[i]['auc_l']
        predictable_n.append(((t/0.5)>1).sum())

        # number of predictable variables by fdr control criterion
        alpha = 0.05 # desired control level for FDR
        slope = alpha/res[i].shape[0]

        below = res[i]['p_val'].values <= slope * np.array(list(range(1,1+res[i]['p_val'].shape[0])))
        if sum(below) > 0:
            tot_fdr = np.max(np.where(below)[0])+1
        else:
            tot_fdr = 0

        predictable_n_fdr.append(tot_fdr)

    predictable_n_fdr = np.array(predictable_n_fdr)
    predictable_n = np.array(predictable_n)

    # plotting
    plt.figure(figsize=(6,3), dpi=300)

    plt.plot(predictable_n_fdr, model_names, '-o', color=colors[0], label='BH(0.05) significance')
    plt.plot(predictable_n, model_names, '--D', color=colors[9], label='2SE significance')

    plt.xlabel('Number of predictable variables')
    plt.gca().invert_yaxis()

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)   

    plt.grid(axis='both', alpha=.4, linewidth=.1)

    plt.legend(loc=1,fontsize='small')

    plt.savefig(saved+'.pdf', bbox_inches='tight', transparent=True)
    plt.close()

    pd.DataFrame([model_names,predictable_n.tolist(),predictable_n_fdr.tolist()]).to_csv(saved+'.csv',index=False)







paths = [
    RESULTS+'/crossvalidation_auc_demographics.csv',
    RESULTS+'/crossvalidation_auc_demographics_shallowfacemetrics.csv',
    RESULTS+'/crossvalidation_auc_all_plus_img.csv'
    ]


model_names = [
    'Demographics (age, gender, race)',
    'Demographics + face metrics (e.g., width/height)',
    'Demographics + face metrics + deep image features'
    ]

waterfall(paths, model_names, RESULTS+'/waterfall_short')



# avg. auc by model
def auc_avg(paths, model_names, saved):

    avg_auc = []

    for p in paths:

        temp = pd.read_csv(p)
        temp = temp.stack().reset_index()
        temp.columns = ['cv_fold', 'var_name', 'auc']

        # calculating mean AUC mean and sd across cv folds for each variable
        temp = temp[['var_name', 'auc']].groupby(['var_name'],sort=False).agg(['mean','std']).reset_index()
        temp.columns = temp.columns.map('_'.join).str.strip('_')

        avg_auc.append(temp['auc_mean'].mean())

    avg_auc = np.array(avg_auc)


    # plotting
    plt.figure(figsize=(6,3), dpi=300)

    plt.plot(avg_auc, model_names, '-o', color=colors[0])

    plt.xlabel('Avg. AUC across 349 variables')
    plt.gca().invert_yaxis()

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)   

    plt.grid(axis='both', alpha=.4, linewidth=.1)

    plt.savefig(saved+'.pdf', bbox_inches='tight', transparent=True)
    plt.close()

    pd.DataFrame([model_names,avg_auc.tolist()]).to_csv(saved+'.csv',index=False)

auc_avg(paths, model_names, RESULTS+'/avg_auc')



np.random.seed(999)
torch.manual_seed(999)

# EXTRACTING RAW IMAGES
def extract_raw_images(loader):

    images = []
    for batch_i, var in enumerate(loader):

        image_batch, _, _ = var
        images.append(image_batch.detach().cpu().numpy())

    images = np.vstack(images).squeeze()
    return images


loader_full = create_dataloader(data,rand=False)
raw_images = extract_raw_images(loader_full)

raw_images= (raw_images - raw_images.min())/ (raw_images.max()-raw_images.min())



# conda install -c conda-forge liblbfgs

# pylbfgs needs to be installed from the following

# https://bitbucket.org/rtaylor/pylbfgs/src/master/
# https://www.chokkan.org/software/liblbfgs/structlbfgs__parameter__t.html#a460f3fc3a4286e58fc1a977ef8803b32
# param.max_linesearch = 100;
# param.past = 10;
# param.delta = 1e-5;
# python setup.py install


from pylbfgs import owlqn

#ind = np.random.choice(raw_images.shape[0],200)
X = np.mean(raw_images, axis=1) # gray images
Y = np.concatenate([data[q_list].values,np.ones((X.shape[0],1))],1) # labels
#Y[Y==0] = -1.

def progress(x, g, fx, xnorm, gnorm, step, k, ls):
    # Print variables to screen or file or whatever. Return zero to 
    # continue algorithm; non-zero will halt execution.
    print('Iteration {}, Loss {}, xnorm {}, gnorm {}'.format(k, fx, xnorm, gnorm))
    return 0



# SYMMETRIC - HALF - OWLQN

_pp = np.zeros(np.prod((Y.shape[1],X.shape[1],X.shape[2]//2)))

def evaluate_symmetric(p, g, step):
    #p=np.ones(np.prod((Y.shape[1],X.shape[1],X.shape[2]//2)))
    np.copyto(_pp,p.squeeze())
    P = p.reshape((Y.shape[1],X.shape[1],X.shape[2]//2))
    P = np.concatenate([P,np.flip(P,2)],2)

    # faster implementation of code commented out below 
    # (due to numpy beung slow o 3D arrays)
    P = P.reshape(Y.shape[1],X.shape[1]*X.shape[2])
    diff = np.dot(Y,P) - X.reshape(X.shape[0],X.shape[1]*X.shape[2])
    loss = np.sum(np.power(diff,2))/X.shape[0]
    grad = 2*np.dot(Y.T,diff) / X.shape[0]
    grad = grad.reshape(Y.shape[1],X.shape[1],X.shape[2])

    # diff = np.dot(Y,P.transpose((1,0,2))) - X
    # loss = np.sum(np.power(diff,2))/X.shape[0]
    # grad = 2*np.dot(Y.T,diff.transpose((1,0,2)))/X.shape[0]

    grad = (grad[:,:,:(X.shape[2]//2)]+np.flip(grad[:,:,(X.shape[2]//2):],2)) #/2
    np.copyto(g,grad.reshape(p.shape))
    return loss

p = owlqn(np.prod((Y.shape[1],X.shape[1],X.shape[2]//2)), evaluate_symmetric, progress, 0.01) # 10


import json
with open(RESULTS+'/feature_shadows_final.json', 'w') as f:
    json.dump(p.tolist(), f)


with open(RESULTS+'/feature_shadows_final.json', 'r') as f:
    p = np.array(json.load(f))



# ANALYZE

P = p.reshape((Y.shape[1],X.shape[1],X.shape[2]//2))
P = np.concatenate([P,np.flip(P,2)],2)

np.mean(1.*(np.abs(P)<=0.001)) # sparsity 0.85

from matplotlib import colors as colorsm
divnorm = colorsm.TwoSlopeNorm(vmin=-1., vcenter=0., vmax=1)

# magnitude
visscore = pd.DataFrame({'Var':[q_to_name_dict[q] for q in q_list] + ['Intercept'],
    'Name':[q_to_full_name_dict[q] for q in q_list] + ['Intercept'],
    'Score':np.abs(P).sum(1).sum(1),
    'Ind':list(range(P.shape[0]))})
visscore = visscore.sort_values('Score', ascending=False)
visscore.iloc[:50]


# VISUAL PROMINENCE SCORE AND AUC PREDICTABILITY!!! HIGLY CORRELATED
visscore = pd.merge(visscore,results_auc,left_on='Name',right_on='var_name_full',how='left',)
visscore[['Score', 'p_val', 'auc_mean']].corr('pearson') # 0.56 (0.31 R^2)
visscore['Score_n'] = (visscore['Score'] - visscore['Score'].iloc[1:].mean())/visscore['Score'].iloc[1:].std()



# plotting image area importance for the first rows x cols variables with significant AUC in a grid
rows = 7
cols = 9

fig = plt.figure(figsize=(22, 23), dpi=300)

fig.gca().spines["top"].set_visible(False)    
fig.gca().spines["bottom"].set_visible(False)    
fig.gca().spines["right"].set_visible(False)    
fig.gca().spines["left"].set_visible(False)  

fig.gca().set_xticks([])
fig.gca().set_yticks([])

fig.subplots_adjust(hspace=0.6, wspace=0.2)

ax = []
for i in range(cols*rows):

    ax.append(fig.add_subplot(rows, cols, i+1))

    var_name = visscore['Var'].iloc[i]
    var_name_full = visscore['Name'].iloc[i]

    ax[-1].set_title("\n".join(wrap(var_name_full, 19)), fontsize=12, fontweight="bold")  # set title
    ax[-1].set_xticks([]) 
    ax[-1].set_yticks([])

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)  

    img = P[visscore.Ind.iloc[i]].copy()
    img = img/np.abs(img).max()

    img = Image.fromarray(np.uint8(plt.cm.get_cmap('gray',9)(divnorm(img))*255.0))
    plt.imshow(img, interpolation='bilinear', aspect='equal')


plt.savefig(RESULTS+'/visual_feature_prominence.pdf', bbox_inches='tight', transparent=True)
plt.close()



selected = ['Q13_0', 'Q13_3', 'Q11_0', 'Q11_1', 'Q12_0', 'Q12_2', 'Q57_21', 'Q6_1_TEXT_0', #'Q6_1_TEXT_1', 
    'Q73', 'Q16_2', 'Q21', 'Q43_1', 'Q28', 'Q24', 'Q56_12', 'Q56_32',  'Q42_28', 'Q48'] 
# white, black, male, female, age0, age2, Snapchat user, iPhone Safari, Chrome, iPhone vs Galaxy pref,  Unemployed and not looking, Body fitness, satisfied with weight,
# Religious, orientation, quarrels, nervous, alcohol, Lifestyle: Smokes too much

# plotting image area importance for the first rows x cols variables with significant AUC in a grid
rows = 2
cols = 9

fig = plt.figure(figsize=(22, 5), dpi=300)

fig.gca().spines["top"].set_visible(False)    
fig.gca().spines["bottom"].set_visible(False)    
fig.gca().spines["right"].set_visible(False)    
fig.gca().spines["left"].set_visible(False)  

fig.gca().set_xticks([])
fig.gca().set_yticks([])

fig.subplots_adjust(hspace=0.6, wspace=0.2)

ax = []
for i in range(cols*rows):

    ax.append(fig.add_subplot(rows, cols, i+1))

    var_name = selected[i]

    #var_name = visscore['Var'].iloc[i]
    var_name_full = visscore['Name'][visscore['var_name']==var_name].item()

    ax[-1].set_title("\n".join(wrap(var_name_full, 19)), fontsize=12, fontweight="bold")  # set title
    ax[-1].set_xticks([]) 
    ax[-1].set_yticks([])

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)  

    img = P[visscore[visscore['var_name']==var_name].Ind.item()].copy()
    img = img/np.abs(img).max()

    img = Image.fromarray(np.uint8(plt.cm.get_cmap('gray',9)(divnorm(img))*255.0))
    plt.imshow(img, interpolation='bilinear', aspect='equal')

plt.savefig(RESULTS+'/visual_feature_prominence_selected.pdf', bbox_inches='tight', transparent=True)
plt.close()



# EXTRACTING RAW IMAGES


# across all images
mean_image = np.transpose(raw_images.mean(0), (1, 2, 0))
mean_image = Image.fromarray(np.uint8(mean_image*255.0))
mean_image.save(RESULTS+'/mean_image.png')

# qualtrics
mean_image = np.transpose(raw_images[data['source']==1].mean(0), (1, 2, 0))
mean_image = Image.fromarray(np.uint8(mean_image*255.0))
mean_image.save(RESULTS+'/mean_image_qualtrics.png')

# mturk
mean_image = np.transpose(raw_images[data['source']==0].mean(0), (1, 2, 0))
mean_image = Image.fromarray(np.uint8(mean_image*255.0))
mean_image.save(RESULTS+'/mean_image_mturk.png')


# creating square tiled image
n = 8
h = 224

# qualtrics tile
qualtrics_imgs = raw_images[data['source']==1]

fig = np.zeros(shape=(h*n,h*n,3))
for i in range(n):
    for j in range(n):
        ind = n*i+j
        img = np.transpose(qualtrics_imgs[ind], (1, 2, 0))
        fig[(i*h):((i+1)*h),(j*h):((j+1)*h)] = img.copy()

tiled_image = Image.fromarray(np.uint8(fig*255.0))
tiled_image.save(RESULTS+'/tiled_image_qualtrics.png')


# mturk tile
mturk_imgs = raw_images[data['source']==0]

fig = np.zeros(shape=(h*n,h*n,3))
for i in range(n):
    for j in range(n):
        ind = n*i+j
        img = np.transpose(mturk_imgs[ind], (1, 2, 0))
        fig[(i*h):((i+1)*h),(j*h):((j+1)*h)] = img.copy()

tiled_image = Image.fromarray(np.uint8(fig*255.0))
tiled_image.save(RESULTS+'/tiled_image_mturk.png')



# VISUALIZING IMAGE AREA IMPORTANCE

#background_image_user_random_id = "00d3d85a3b289caca5e1ce8dcad6f59a0c548ddf9f6a3513377aae440ed7f81e"
background_image = np.transpose(raw_images[37], (1, 2, 0))
background_image = background_image*255.0
background_image = np.dstack((background_image,(np.zeros(shape=(224,224,1))+255)))
background_image = Image.fromarray(np.uint8(background_image))

# create directories to store area importance images
os.makedirs(RESULTS+'/img_imp', exist_ok=True)
os.makedirs(RESULTS+'/img_imp_background', exist_ok=True)

# path importance loading
patch_importance = json.loads(open(RESULTS+'/patch_importance.json').read())

for q in q_list:
    arr = np.array(patch_importance[q])
    arr = (arr - arr.min())/(arr.max()-arr.min())

    im = Image.fromarray(np.uint8(plt.cm.get_cmap('YlOrRd')(arr)*255.0))
    im.save(RESULTS+'/img_imp/'+q_to_name_dict[q]+'.png')

    im = np.uint8((plt.cm.get_cmap('YlOrRd')(arr))*255.0)
    im[:,:,3] = 128
    im = Image.fromarray(im)
    im = Image.alpha_composite(background_image, im)
    im.save(RESULTS+'/img_imp_background/'+q_to_name_dict[q]+'.png')


# plotting image area importance for the first rows x cols variables with significant AUC in a grid
rows = 7
cols = 9

fig = plt.figure(figsize=(22, 23), dpi=300)

fig.gca().spines["top"].set_visible(False)    
fig.gca().spines["bottom"].set_visible(False)    
fig.gca().spines["right"].set_visible(False)    
fig.gca().spines["left"].set_visible(False)  

fig.gca().set_xticks([])
fig.gca().set_yticks([])

fig.subplots_adjust(hspace=0.6, wspace=0.2)

ax = []
for i in range(cols*rows):

    ax.append(fig.add_subplot(rows, cols, i+1))

    var_name = results_auc_filtered['var_name'].iloc[i]
    var_name_full = results_auc_filtered['var_name_full'].iloc[i]

    ax[-1].set_title("\n".join(wrap(var_name_full, 19)), fontsize=12, fontweight="bold")  # set title
    ax[-1].set_xticks([]) 
    ax[-1].set_yticks([])

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)  

    img=mpimg.imread(RESULTS+'/img_imp_background/'+q_to_name_dict[var_name]+'.png')
    plt.imshow(img, interpolation='bilinear', aspect='equal') 

plt.savefig(RESULTS+'/importance_tile.pdf', bbox_inches='tight', transparent=True)
plt.close()



# plotting image area importance for the first rows x cols variables 
# for selected variables
selected = ['Q13_0', 'Q13_3', 'Q11_0', 'Q11_1', 'Q12_0', 'Q12_2', 'Q57_21', 'Q6_1_TEXT_0', #'Q6_1_TEXT_1', 
    'Q73', 'Q16_2', 'Q21', 'Q43_1', 'Q28', 'Q24', 'Q56_12', 'Q56_32', 'Q42_28', 'Q48'] 
# white, black, male, female, age0, age2, Snapchat user, iPhone Safari, Chrome, iPhone vs Galaxy pref,  Unemployed and not looking, Body fitness, satisfied with weight,
# Religious, orientation, quarrels, nervous, alcohol, Lifestyle: Smokes too much


rows = 2
cols = 9

fig = plt.figure(figsize=(22, 5), dpi=300)

fig.gca().spines["top"].set_visible(False)    
fig.gca().spines["bottom"].set_visible(False)    
fig.gca().spines["right"].set_visible(False)    
fig.gca().spines["left"].set_visible(False)  

fig.gca().set_xticks([])
fig.gca().set_yticks([])

fig.subplots_adjust(hspace=0.6, wspace=0.2)

ax = []
for i in range(cols*rows):

    ax.append(fig.add_subplot(rows, cols, i+1))

    var_name = selected[i]
    var_name_full = results_auc_filtered['var_name_full'][results_auc_filtered['var_name']==var_name].item()

    ax[-1].set_title("\n".join(wrap(var_name_full, 19)), fontsize=12, fontweight="bold")  # set title
    ax[-1].set_xticks([]) 
    ax[-1].set_yticks([])

    plt.gca().spines["top"].set_visible(False)    
    plt.gca().spines["bottom"].set_visible(False)    
    plt.gca().spines["right"].set_visible(False)    
    plt.gca().spines["left"].set_visible(False)  

    img=mpimg.imread(RESULTS+'/img_imp_background/'+q_to_name_dict[var_name]+'.png')
    plt.imshow(img, interpolation='bilinear', aspect='equal') 

plt.savefig(RESULTS+'/importance_tile_selected.pdf', bbox_inches='tight', transparent=True)
plt.close()




# finetuning the final model - on all data - so that we have a copy

np.random.seed(999)
torch.manual_seed(999)
loader_full_rand = create_dataloader(data,rand=True)
#finetune_and_save(loader_full_rand, loader_full_rand) # training model on all of the data
model = get_pretrained(finetuned=True)



# CORRELATION ANALYSIS

np.random.seed(999)
torch.manual_seed(999)

loader_full = create_dataloader(data, rand=False)
X_raw, Y, Z = extract_data(loader_full, model)
svd = TruncatedSVD(n_components=500, random_state=0, n_iter=100).fit(X_raw)
X = svd.transform(X_raw)
Y_df = pd.DataFrame(Y, columns=q_list)
Y_demographics = Y_df[demographic_vars]
Y_demographics = pd.merge(Y_demographics,dem_ref,on=demographic_vars,sort=False,how='left')
Y_demographics = Y_demographics.values # [dem_code_var]

browser_vars = ['Q6_1_TEXT_0', 'Q6_1_TEXT_1']
Y_browser = Y_df[browser_vars].values

inp = np.concatenate([X, Y_demographics, Y_browser, Z],1)
out = Y


# smoking feature Q42_28
coefs = np.abs(np.corrcoef(np.concatenate([Y_df['Q42_28'].values.reshape(-1,1), X],1).T)[1:,0])
smoke_comp = np.argmax(coefs)

# # smoking feature Q42_28
# clf = ridge_regression(X, Y_df['Q42_28'].values)
# coefs = np.abs(clf.coef_)
# smoke_comp = np.argmax(coefs)

selected = ['Q13_0', 'Q13_3', 'Q11_0', 'Q11_1', 'Q12_0', 'Q12_2', 'Q57_21', 'Q6_1_TEXT_0', #'Q6_1_TEXT_1', 
    'Q73', 'Q16_2', 'Q21', 'Q43_1', 'Q28', 'Q24', 'Q56_12', 'Q56_32',  'Q42_28', 'Q48'] 
# white, black, male, female, age0, age2, Snapchat user, iPhone Safari, Chrome, iPhone vs Galaxy pref,  Unemployed and not looking, Body fitness, satisfied with weight,
# Religious, orientation, quarrels, nervous, Lifestyle: Smokes too much, alcohol

Z_df = pd.DataFrame(Z, columns=im_list)
Z_df['smoking_feature'] = X[:,smoke_comp]

temp = pd.concat([Y_df,Z_df],1)
rho = temp[Z_df.columns.tolist()+selected].corr()
rho = rho.loc[selected,Z_df.columns.tolist()]
rho.index = [q_to_full_name_dict[q] for q in rho.index]
rho.round(2).to_csv(RESULTS+'/face_metrics_correlations.csv')

# # significance - all corr. significant above ~0.05
# from scipy.stats import t
# tt = t.ppf(1-0.01/2,df=Y.shape[0]-2)
# tt/np.sqrt(Y.shape[0]-2+tt**2)


# individual-clustered standard errors for correlation coefficient

X = temp[Z_df.columns.tolist()+selected].copy()
clusters = data['randomID']
corr, corr_pval = correlate_clustered(X, clusters) 

corr = corr.loc[selected,Z_df.columns.tolist()]
corr_pval = corr_pval.loc[selected,Z_df.columns.tolist()]

corr.index = [q_to_full_name_dict[q] for q in corr.index]
corr_pval.index = [q_to_full_name_dict[q] for q in corr_pval.index]

corr.round(2).to_csv(RESULTS+'/face_metrics_correlations.csv')
corr_pval.round(3).to_csv(RESULTS+'/face_metrics_correlations_pval.csv')

corr_sig = corr_pval<=0.01
corr_sig.to_csv(RESULTS+'/face_metrics_correlations_sign.csv')

# all coef values above this threshold are significant (>= 0.072~0.8)
corr[~corr_sig].abs().max().max()

# all coef values below this threshold are insignificant (<= 0.06)
corr[corr_sig].abs().min().min()




# PREDICTIONS FROM IMAGES

lin_models = []
for i in range(len(q_list)): #tqdm
    clf = ridge_regression(X, Y[:,i])
    lin_models.append(clf)


preds = []
for i in range(Y.shape[1]):
    mod = lin_models[i]
    y_prob = mod.predict(X)
    preds.append(y_prob)


preds = pd.DataFrame(preds).T
preds.columns = q_list
preds.to_csv(RESULTS+'/pipeline_predictions.csv', index=False)




