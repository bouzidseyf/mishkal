﻿#!/usr/bin/python
# -*- coding = utf-8 -*-
#-----------------------------------------------------------------------
# Name:        stem_verb
# Purpose:     Arabic lexical analyser, provides feature for 
#  stemming arabic word as verb
#
# Author:      Taha Zerrouki (taha.zerrouki[at]gmail.com)
#
# Created:     31-10-2011
# Copyright:   (c) Taha Zerrouki 2011
# Licence:     GPL
#-----------------------------------------------------------------------
"""
    Arabic verb stemmer
"""
import re
import pyarabic.araby as araby
import tashaphyne.stemming
import qalsadi.stem_verb_const as svconst
#~import analex_const 
import libqutrub.classverb   
import arramooz.arabicdictionary as arabicdictionary 
import qalsadi.wordcase as wordcase
#~ import  stemmedword

class VerbStemmer:
    """
        Arabic verb stemmer
    """

    def __init__(self, debug = False):
        # create a stemmer object for stemming enclitics and procletics
        self.comp_stemmer = tashaphyne.stemming.ArabicLightStemmer() 

        # configure the stemmer object
        self.comp_stemmer.set_infix_letters(svconst.COMP_INFIX_LETTERS) 
        self.comp_stemmer.set_prefix_letters(svconst.COMP_PREFIX_LETTERS) 
        self.comp_stemmer.set_suffix_letters(svconst.COMP_SUFFIX_LETTERS) 
        self.comp_stemmer.set_max_prefix_length(svconst.COMP_MAX_PREFIX) 
        self.comp_stemmer.set_max_suffix_length(svconst.COMP_MAX_SUFFIX) 
        self.comp_stemmer.set_min_stem_length(svconst.COMP_MIN_STEM) 
        self.comp_stemmer.set_prefix_list(svconst.COMP_PREFIX_LIST) 
        self.comp_stemmer.set_suffix_list(svconst.COMP_SUFFIX_LIST) 


        # create a stemmer object for stemming conjugated verb
        self.conj_stemmer = tashaphyne.stemming.ArabicLightStemmer() 

        # configure the stemmer object
        self.conj_stemmer.set_infix_letters(svconst.CONJ_INFIX_LETTERS) 
        self.conj_stemmer.set_prefix_letters(svconst.CONJ_PREFIX_LETTERS) 
        self.conj_stemmer.set_suffix_letters(svconst.CONJ_SUFFIX_LETTERS) 
        self.conj_stemmer.set_max_prefix_length(svconst.CONJ_MAX_PREFIX) 
        self.conj_stemmer.set_max_suffix_length(svconst.CONJ_MAX_SUFFIX) 
        self.conj_stemmer.set_min_stem_length(svconst.CONJ_MIN_STEM) 
        self.conj_stemmer.set_prefix_list(svconst.CONJ_PREFIX_LIST) 
        self.conj_stemmer.set_suffix_list(svconst.CONJ_SUFFIX_LIST) 
        # enable the last mark (Harakat Al-I3rab) 
        self.allow_syntax_lastmark  = True  

        # To show statistics about verbs
        #~statistics = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0, 6:0, 7:0, 8:0, 9:0,
         #~10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0, 17:0, 18:0, 19:0, 20:0, 
        #~}

        self.debug = debug 
        self.cache_verb = {'verb':{}}
    
        self.verb_dictionary = arabicdictionary.ArabicDictionary("verbs")

        self.verb_stamp_pat = re.compile(u"[%s%s%s%s%s]"%( araby.ALEF, 
        araby.YEH, araby.WAW, araby.ALEF_MAKSURA, araby.SHADDA), re.UNICODE)

    def stemming_verb(self, verb):
        """
        Stemming verb
        @param verb: given verb
        @type verb: unicode
        @return : stemmed words
        @rtype:
        """
        list_found  =  [] 
        #~display_conj_result = False 
        detailed_result  =  [] 
        verb             =  verb.strip() 
        verb_list         =  [verb] 
        if verb.startswith(araby.ALEF_MADDA):
            verb_list.append(araby.ALEF_HAMZA_ABOVE + araby.ALEF_HAMZA_ABOVE \
            +verb[1:])
            verb_list.append(araby.HAMZA+araby.ALEF+verb[1:])

        for verb in verb_list:

            list_seg_comp = self.comp_stemmer.segment(verb) 
            for seg in list_seg_comp:
                procletic = verb[:seg[0]] 
                stem = verb[seg[0]:seg[1]]
                encletic = verb[seg[1]:]
                #~secondsuffix = u'' 
                # حالة الفعل المتعدي لمفعولين
                if svconst.TableDoubleTransitiveSuffix.has_key(encletic ):
                    firstsuffix = \
                    svconst.TableDoubleTransitiveSuffix[encletic]['first'] 
                    encletic = firstsuffix 

                list_stem = [stem] 
                if encletic:  #! = "":
                    transitive = True 
                    if stem.endswith(araby.TEH + araby.MEEM + araby.WAW):
                        list_stem.append(stem[:-1]) 
                    elif stem.endswith(araby.WAW):
                        list_stem.append(stem+ araby.ALEF) 
                    elif stem.endswith( araby.ALEF):
                        list_stem.append(stem[:-1]+ araby.ALEF_MAKSURA) 

                else: transitive = False 
                if verb.startswith(araby.ALEF_MADDA):
                    # االبداية بألف مد
                    list_stem.append(araby.ALEF_HAMZA_ABOVE + \
                    araby.ALEF_HAMZA_ABOVE+verb[1:])
                    list_stem.append(araby.HAMZA+ araby.ALEF+verb[1:])

        # stem reduced verb : level two
                result = [] 
                for verb2 in list_stem:
                    #segment the coinjugated verb
                    list_seg_conj = self.conj_stemmer.segment(verb2) 

                    # verify affix compatibility
                    list_seg_conj  =  verify_affix(verb2, list_seg_conj, 
                    svconst.VERBAL_CONJUGATION_AFFIX) 
                    # verify procletics and enclitecs
                    # verify length pof stem
                    list_seg_conj2 = [] 
                    for seg_conj in list_seg_conj:
                        if (seg_conj[1] - seg_conj[0]) <= 6 :
                            prefix_conj   =  verb2[:seg_conj[0]] 
                            stem_conj     =  verb2[seg_conj[0]:seg_conj[1]]
                            suffix_conj   =  verb2[seg_conj[1]:]
                            affix_conj    =  prefix_conj+'-'+suffix_conj 


                        # verify compatibility between procletics and afix
                            if (is_compatible_proaffix_affix(procletic, 
                            encletic, affix_conj)):
                                # verify the existing of a verb stamp in 
                                #the dictionary
                                if self.verb_dictionary.exists_as_stamp(
                                   stem_conj):
                                    list_seg_conj2.append(seg_conj)

                    list_seg_conj      =  list_seg_conj2 
                    list_correct_conj  =  [] 

                    for seg_conj in list_seg_conj:
                        prefix_conj  =  verb2[:seg_conj[0]] 
                        stem_conj    =  verb2[seg_conj[0]:seg_conj[1]]
                        suffix_conj  =  verb2[seg_conj[1]:]
                        affix_conj   =  '-'.join([prefix_conj, suffix_conj])

                            
                        # search the verb in the dictionary by stamp
                        # if the verb exists in dictionary, 
                        # The transitivity is consedered
                        # if is trilateral return its forms and Tashkeel
                        # if not return forms without tashkeel, 
                        #because the conjugator can vocalized it, 
                        # we can return the tashkeel if we don't need the 
                        #conjugation step  
                        infverb_dict = self.get_infinitive_verb_by_stem(
                        stem_conj, transitive) 

                        infverb_dict  =  self.verify_infinitive_verbs(stem_conj,
                         infverb_dict) 
                            

                        for item in infverb_dict:
                            #The haraka from is given from the dict
                            inf_verb      =  item['verb'] 
                            haraka        =  item['haraka'] 
                            transtag      =   item['transitive'] 
                            transitive     =   (item['transitive'] == 'y' \
                            or not item['transitive']) 

                            original_tags  =  transtag  
                            # dict tag is used to mention word dictionary tags:
                            # the original word tags like transitive attribute
                            unstemed_verb =  verb2 

                            # conjugation step

                            # ToDo, conjugate the verb with affix, 
                            # if exists one verb which match, return it
                            # تصريف الفعل مع الزوائد
                            # إذا توافق التصريف مع الكلمة الناتجة
                            # تعرض النتيجة
                            onelist_correct_conj  =  [] 
                            onelist_correct_conj  =  generate_possible_conjug(
                            inf_verb, unstemed_verb, affix_conj, haraka, 
                            procletic, encletic, transitive) 

                            if len(onelist_correct_conj)>0:
                                list_correct_conj += onelist_correct_conj 
                    for conj in list_correct_conj:
                        result.append(conj['verb'])

                        detailed_result.append(wordcase.WordCase({
                        'word':verb, 
                        'affix': ( procletic, prefix_conj, suffix_conj, 
                        encletic),                      
                        #~ 'procletic':procletic, 
                        #~ 'encletic':encletic, 
                        #~ 'prefix':prefix_conj, 
                        #~ 'suffix':suffix_conj, 
                        'stem':stem_conj, 
                        'original':conj['verb'], 
                        'vocalized':vocalize(conj['vocalized'], procletic,
                         encletic), 
                        'tags':u':'.join((conj['tense'], conj['pronoun'])+\
                        svconst.COMP_PREFIX_LIST_TAGS[procletic]['tags']+\
                        svconst.COMP_SUFFIX_LIST_TAGS[encletic]['tags']), 
                        'type':'Verb', 
                        #~ 'root':'', 
                        #~ 'template':'', 
                        'freq':'freqverb', 
                        'originaltags':original_tags, 
                        'syntax':'', 
                        })) 

                list_found += result 

        list_found = set(list_found) 
        return detailed_result

    
    def get_infinitive_verb_by_stem(self, verb, transitive):
        """
        Get the infinitive verb form by given stem, and transitivity
        @param verb: the given verb
        @type verb; unicode
        @param transitive: tranitive or intransitive
        @type transitive: boolean
        @return : list of infinitive verbs
        @rtype: list of unicode
        """
        # a solution by using verbs stamps
        liste = [] 
        
        verb_id_list = self.verb_dictionary.lookup_by_stamp(verb) 

        if len(verb_id_list):
            for verb_tuple in verb_id_list:
                liste.append({'verb':verb_tuple['vocalized'], 
                'transitive':verb_tuple['transitive'], 
                'haraka':verb_tuple['future_type']}) 

        # if the verb in dictionary is vi and the stemmed verb is vt, 
        #~don't accepot
        listetemp = liste 
        liste = []
        for item in listetemp:
            ##        print item['transitive'].encode("utf8"), transitive
            if item['transitive'] == u'y' or  not transitive:
                liste.append(item) 

        return liste 



      

    def set_debug(self, debug):
        """
        Set the debug attribute to allow printing internal analysis results.
        @param debug: the debug value.
        @type debug: True/False.
        """
        self.debug = debug 
    def enable_syntax_lastmark(self):
        """
        Enable the syntaxic last mark attribute to allow use of I'rab harakat.
        """
        self.allow_syntax_lastmark = True 

    def disable_syntax_lastmark(self):
        """
        Disable the syntaxic last mark attribute to allow use of I'rab harakat.
        """
        self.allow_syntax_lastmark = False 


    def verify_infinitive_verbs(self, stem_conj, infverb_dict):
        """
        verify if given infinitive verbs are compatible with stem_conj
        @param stem_conj: the stemmed verbs without conjugation affixes.
        @type stem_conj: unicode.
        @param infverb_dict: list of given infinitive verbs, 
        each item contain 'verb' and 'type'.
        @type infverb_dict: list of dicts.
        @return: filtred  infinitive verbs
        @rtype: list of dict
        """
        tmp = [] 
        stem_stamp = self.verb_stamp(stem_conj) 
        for item in infverb_dict:
            if self.verb_stamp(item['verb']) == stem_stamp:
                tmp.append(item) 
        return tmp  


    def verb_stamp(self, word):
        """
        generate a stamp for a verb, 
        the verb stamp is different of word stamp, by hamza noralization
        remove all letters which can change form in the word :
        - ALEF, 
        - YEH, 
        - WAW, 
        - ALEF_MAKSURA
        - SHADDA
        @return: stamped word
        """
        word = araby.strip_tashkeel(word) 
        #The vowels are striped in stamp function
        word = araby.normalize_hamza(word) 
        if word.startswith(araby.HAMZA):
            #strip The first hamza
            word = word[1:] 
        # strip the last letter if is doubled
        if word[-1:] ==  word[-2:-1]:
            word = word[:-1] 
        return self.verb_stamp_pat.sub('', word)





def is_compatible_proaffix_affix(procletic, encletic, affix):
    """
    Verify if proaffixes (sytaxic affixes) are compatable with affixes 
    (conjugation) 
    @param procletic: first level prefix.
    @type procletic: unicode.
    @param encletic: first level suffix.
    @type encletic: unicode.
    @param affix: second level affix.
    @type affix: unicode.
    @return: compatible.
    @rtype: True/False.
    """    
    if not procletic and not encletic:
        return True 
    else:
        procletic_compatible = False 
        if not procletic :
            procletic_compatible = True
        elif svconst.ExternalPrefixTable.has_key(procletic):
            if affix == '-':
                procletic_compatible = True 
            else:
                for item in svconst.Table_affix.get(affix, []):
                    #the tense item[0] 
                    if item[0] in svconst.ExternalPrefixTable.get(procletic,
                     ''):
                        procletic_compatible = True 
                        break 
                else:
                    procletic_compatible = False 

        if procletic_compatible:
            if not encletic :
                return True 
            elif svconst.ExternalSuffixTable.has_key(encletic):
                if affix == '-':
                    return True 
                else: 
                    for item in svconst.Table_affix.get(affix, []):
                        #the tense item[0] 
                        if item[1] in svconst.ExternalSuffixTable.get(encletic,
                         ''):
                            return True 
                    else:
                        return False 
    return False 


def is_compatible_proaffix_tense(procletic, encletic, tense, pronoun, 
   transitive):
    """
    test if the given tenses are compatible with procletics
    """
    # إذا كان الزمن مجهولا لا يرتبط مع الفعل اللازم
    if not transitive and tense in svconst.qutrubVerbConst.TablePassiveTense:
        return False 
    if not procletic and not encletic:
        return True 
    # The passive tenses have no encletics
    #ﻷزمنة المجهولة ليس لها ضمائر متصلة في محل نصب مفعول به
    #لأنّ مفعولها يصبح نائبا عن الفاعل
    
    if encletic and tense in svconst.qutrubVerbConst.TablePassiveTense:
        return False 
    elif (not procletic or tense in \
    svconst.ExternalPrefixTable.get(procletic, ''))\
        and (not encletic or pronoun in \
        svconst.ExternalSuffixTable.get(encletic, '')):
        return True 
    else:
        return False 
def verify_affix(word, list_seg, affix_list):
    """
    Verify possible affixes in the resulted segments 
    according to the given affixes list.
    @param word: the input word.
    @type word: unicode.
    @param list_seg: list of word segments indexes (numbers).
    @type list_seg: list of pairs.
    @return: list of acceped segments.
    @rtype: list of pairs.
    """ 
    return [s for s in list_seg if '-'.join([word[:s[0]], 
       word[s[1]:]]) in affix_list]    
    #~return filter (lambda s: '-'.join([word[:s[0]], 
    #~word[s[1]:]]) in affix_list, list_seg)
def get_enclitic_variant(word, enclitic):

    """
    Get the enclitic variant to be joined to the word.
    For example: word  =  أرجِهِ , encletic = هُ. 
    The enclitic  is convert to HEH+ KAsra.
    اعبارة في مثل أرجه وأخاه إلى يم الزينة
    @param word: word found in dictionary.
    @type word: unicode.
    @param enclitic: first level suffix vocalized.
    @type enclitic: unicode.
    @return: variant of enclitic.
    @rtype: unicode.
    """
    #if the word ends by a haraka
    if enclitic == araby.HEH+araby.DAMMA and (word.endswith(araby.KASRA)\
     or word.endswith(araby.YEH)):
        enclitic = araby.HEH+araby.KASRA 
    return enclitic 

def vocalize(verb, proclitic, enclitic):
    """
    Join the  verb and its affixes, and get the vocalized form
    @param verb: verb found in dictionary.
    @type verb: unicode.
    @param proclitic: first level prefix.
    @type proclitic: unicode.
    @param enclitic: first level suffix.
    @type enclitic: unicode.        
    @return: vocalized word.
    @rtype: unicode.
    """    
    enclitic_voc   =  svconst.COMP_SUFFIX_LIST_TAGS[enclitic]["vocalized"][0] 
    enclitic_voc   =  get_enclitic_variant(verb, enclitic_voc)
    proclitic_voc  =  svconst.COMP_PREFIX_LIST_TAGS[proclitic]["vocalized"][0] 
    #suffix_voc = suffix #CONJ_SUFFIX_LIST_TAGS[suffix]["vocalized"][0] 
    # لمعالجة حالة ألف التفريق
    if enclitic and verb.endswith(araby.WAW+ araby.ALEF) :
        verb  =  verb[:-1] 
    if enclitic and verb.endswith(araby.ALEF_MAKSURA):
        verb  =  verb[:-1]+araby.ALEF 
    return ''.join([ proclitic_voc, verb , enclitic_voc]) 


def generate_possible_conjug(infinitive_verb, unstemed_verb , affix, 
future_type = araby.FATHA, extern_prefix = "-", extern_suffix = "-", 
transitive = True):
    """
    generate possible conjugation for given verb to be stemmed
    """
##    future_type = FATHA 
    #~ transitive = True 
    list_correct_conj = [] 
    if infinitive_verb == "" or unstemed_verb == "" or affix == "":
        return set() 
    vbc  =  libqutrub.classverb.VerbClass(infinitive_verb, transitive,
     future_type)
    # الألف ليست جزءا من السابقة، لأنها تستعمل لمنع الابتداء بساكن
    # وتصريف الفعل في الامر يولده
    if affix.startswith(araby.ALEF):
        affix = affix[1:]
    # get all tenses to conjugate the verb one time
    tenses = [] 
    if svconst.Table_affix.has_key(affix):
        for pair in svconst.Table_affix[affix]:
            tenses.append(pair[0]) #tense = pair[0]
    tenses = list(set(tenses))  # avoid duplicata 


    if svconst.Table_affix.has_key(affix):
        for pair in svconst.Table_affix[affix]:
            tense = pair[0]
            pronoun = pair[1]
            if is_compatible_proaffix_tense(extern_prefix, extern_suffix, 
            tense, pronoun, transitive):

                conj_vocalized  =  vbc.conjugate_tense_for_pronoun( tense,
                 pronoun)
                #strip all marks and shadda
                conj_nm  =   araby.strip_tashkeel(conj_vocalized) 
                if conj_nm == unstemed_verb:
                    list_correct_conj.append({'verb':infinitive_verb, 
                    'tense':tense, 'pronoun':pronoun, 
                    'vocalized':conj_vocalized, 'unvocalized':conj_nm}) 
    return list_correct_conj 

def mainly():
    """
    Test main"""
    #ToDo: use the full dictionary of arramooz
    wordlist = [u'يضرب', u"استقلّ", u'استقل', ]
    verbstemmer = VerbStemmer() 
    verbstemmer.set_debug(True) 
    for word in wordlist:
        verbstemmer.conj_stemmer.segment(word) 
        print verbstemmer.conj_stemmer.get_affix_list() 
    for word in wordlist:
        result = verbstemmer.stemming_verb(word) 
        for analyzed in  result:
            print repr(analyzed) 
            print u'\n'.join(analyzed.keys()) 
            for key in analyzed.keys():
                print u'\t'.join([key, unicode(analyzed[key])]).encode('utf8')
            print 
            print 
#Class test
if __name__  ==  '__main__':
    mainly()