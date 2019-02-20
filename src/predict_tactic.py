#!/usr/bin/env python3.7

import torch
from typing import Dict, List, Union
from models.tactic_predictor import TacticPredictor

from models import encdecrnn_predictor
from models import try_common_predictor
from models import wordbagclass_predictor
from models import ngramclass_predictor
from models import encclass_predictor
from models import dnnclass_predictor
from models import k_nearest_predictor
from models import autoclass_predictor
from models import wordbagsvm_classifier
from models import ngramsvm_classifier
from models import hyparg_predictor
from models import pec_predictor
from models import features_predictor
from models import encfeatures_predictor
from models import featuressvm_predictor
from models import regex_predictor

from typing import Dict, Callable, List

predictors = {
    'encdec' : encdecrnn_predictor.EncDecRNNPredictor,
    'encclass' : encclass_predictor.EncClassPredictor,
    'dnnclass' : dnnclass_predictor.DNNClassPredictor,
    'trycommon' : try_common_predictor.TryCommonPredictor,
    'wordbagclass' : wordbagclass_predictor.WordBagClassifyPredictor,
    'ngramclass' : ngramclass_predictor.NGramClassifyPredictor,
    'k-nearest' : k_nearest_predictor.KNNPredictor,
    'autoclass' : autoclass_predictor.AutoClassPredictor,
    'wordbagsvm' : wordbagsvm_classifier.WordBagSVMClassifier,
    'ngramsvm' : ngramsvm_classifier.NGramSVMClassifier,
    'hyparg' : hyparg_predictor.HypArgPredictor,
    'pec' : pec_predictor.PECPredictor,
    'features' : features_predictor.FeaturesPredictor,
    'featuressvm' : featuressvm_predictor.FeaturesSVMPredictor,
    'encfeatures' : encfeatures_predictor.EncFeaturesPredictor,
    'regex' : regex_predictor.RegexPredictor,
}

trainable_models : Dict[str, Callable[[List[str]], None]] = {
    "encclass" : encclass_predictor.main,
    "encdec" : encdecrnn_predictor.main,
    "dnnclass" : dnnclass_predictor.main,
    "trycommon" : try_common_predictor.train,
    "wordbagclass" : wordbagclass_predictor.main,
    "ngramclass" : ngramclass_predictor.main,
    "k-nearest" : k_nearest_predictor.main,
    "autoclass" : autoclass_predictor.main,
    "wordbagsvm" : wordbagsvm_classifier.main,
    "ngramsvm" : ngramsvm_classifier.main,
    "hyparg" : hyparg_predictor.main,
    "pec" : pec_predictor.main,
    "features" : features_predictor.main,
    "encfeatures" : encfeatures_predictor.main,
    "featuressvm" : featuressvm_predictor.main,
    'regex' : regex_predictor.main,
}

def loadPredictor(filename : str, predictor_type : str) -> TacticPredictor:
    # Silencing the type checker on this line because the "real" type
    # of the predictors dictionary is "string to classes constructors
    # that derive from TacticPredictor, but are not tactic
    # predictor". But I don't know how to specify that.
    predictor = predictors[predictor_type]() # type: ignore
    predictor.load_saved_state(*torch.load(filename))
    return predictor
