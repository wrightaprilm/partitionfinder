import logging
log = logging.getLogger("analysis_method")

import os
import scheme
import algorithm
import submodels
from analysis import Analysis, AnalysisError

class UserAnalysis(Analysis):

    def do_analysis(self):
        """Process everything when search=user"""
        models = self.cfg.models

        current_schemes = [s for s in self.cfg.schemes]
        self.total_scheme_num = len(current_schemes)
        if self.total_scheme_num>0:
            for s in current_schemes:
                 self.analyse_scheme(s, models)
        else:
            log.error("Search set to 'user', but no user schemes detected in .cfg file. Please check.")
            raise AnalysisError

class AllAnalysis(Analysis):

    def do_analysis(self):
        models = self.cfg.models
        partnum = len(self.cfg.partitions)

        self.total_scheme_num = submodels.count_all_schemes(partnum)
        log.info("Analysing all possible schemes for %d starting partitions", partnum)
        log.info("This will result in %s schemes being created", self.total_scheme_num)
        self.total_subset_num = submodels.count_all_subsets(partnum)
        log.info("PartitionFinder will have to analyse %d subsets to complete this analysis" %(self.total_subset_num))
        if self.total_subset_num>10000:
            log.warning("%d is a lot of subsets, this might take a long time to analyse", self.total_subset_num)
            log.warning("Perhaps consider using a different search scheme instead (see Manual)")

        #clear any schemes that are currently loaded
        self.cfg.schemes.clear_schemes()

        #iterate over submodels, which we can turn into schemes afterwards in the loop
        model_iterator = submodels.submodel_iterator([], 1, partnum)

        scheme_name = 1
        for m in model_iterator:
            s = scheme.model_to_scheme(m, scheme_name, self.cfg)
            scheme_name = scheme_name+1
            self.analyse_scheme(s, models)

class GreedyAnalysis(Analysis):

    def get_score(self, my_result):
        #TODO: this is bad. Should use self.cfg.model_selection, or write
        #a new model_selection for scheme.py
        model_selection = self.cfg.model_selection
        if model_selection=="aic":
            score=my_result.aic
        elif model_selection=="aicc":
            score=my_result.aicc
        elif model_selection=="bic":
            score=my_result.bic
        else:
            log.error("Unrecognised model_selection variable '%s', please check" %(score))
            raise AnalysisError
        return score
    
    def get_best_scheme_from_list(self, scheme_description_list):
        """
        Take a list of scheme descriptions, analyse them all, and return the best one
        """
        self.cfg.schemes.clear_schemes()        
        best_score = None
        cur_s = 1
        for description in scheme_description_list:

            newscheme = scheme.create_scheme(self.cfg, cur_s, description)
            cur_s += 1
            newscheme.result = self.analyse_scheme(newscheme, self.cfg.models)
            newscheme.score = self.get_score(newscheme.result)
            newscheme.description = description
    
            if best_score==None or newscheme.score < best_score:
                best_score  = newscheme.score
                best_scheme = newscheme

        return best_scheme                

    def do_forwards_analysis(self):
        '''A greedy algorithm for heuristic partitioning searches
        This one does a quick pass using just HKY+G model to get an OK starting scheme
        '''
        log.info("Performing greedy analysis")
        partnum = len(self.cfg.partitions)
        models = self.cfg.models

        #start with the most partitioned scheme
        start_description = range(len(self.cfg.partitions))
        start_scheme = scheme.create_scheme(self.cfg, 1, start_description)
        log.info("Analysing fully partitioned scheme")
        result = self.analyse_scheme(start_scheme, models)
        
        best_result = result
        best_score  = self.get_score(result)
                
        step = 1
        cur_s = 2

        #now we try out all lumpings of the current scheme, to see if we can find a better one
        #and if we do, we just keep going
        while True:
            log.info("***Greedy analysis step %s***" % step)
            #get a list of all possible lumpings of the best_scheme
            lumpings = algorithm.lumpings(start_description)
            
            self.cfg.schemes.clear_schemes()        
            best_lumped_scheme = self.get_best_scheme_from_list(lumpings)

            if best_lumped_scheme.score < best_score:
                best_scheme = best_lumped_scheme
                best_score  = best_lumped_scheme.score
                start_description = best_lumped_scheme.description
                if len(set(best_lumped_scheme.description)) == 1: #then it's the scheme with everything equal, so quit
                    break
                step += 1

            else:
                break

        log.info("Best scheme from greedy analysis: %s" % best_scheme)

        return best_scheme

    def do_neighbour_analysis(self, start_scheme):
        '''Start with a scheme, find the best scheme by neighbour searches'''
        models = self.cfg.models        
        self.cfg.schemes.clear_schemes()        
  
        log.info("***Beginning Neighbour Analysis***")
        log.info("Models: %s" % models)
        log.info("Analysing starting scheme")
        start_scheme.result = self.analyse_scheme(start_scheme, models)
        start_scheme.score = self.get_score(start_scheme.result)

        best_result = start_scheme.result
        best_score  = start_scheme.score
        best_scheme = start_scheme
        
        log.info("Starting scheme has score: %.3f" % best_score)
                         
        step = 1
        cur_s = 2
        start_description = start_scheme.description
        
        #now we try out all neighbours of the current scheme, to see if we can find a better one
        #and if we do, we just keep going
        while True:
            log.info("***Neighbour algorithm step %d***" % step)

            #get a list of all possible lumpings of the best_scheme
            neighbours = algorithm.get_neighbours(start_description)
            log.info("Getting neighbours of this scheme: %s" % start_description)
            log.info("Neighbours are: %s" % neighbours)
            self.cfg.schemes.clear_schemes()        
            best_neighbour_scheme = self.get_best_scheme_from_list(neighbours)

            log.info("Best scheme: %s" % best_neighbour_scheme.name)
            log.info("Best score: %.3f" % best_neighbour_scheme.score)

            if best_neighbour_scheme.score < best_score:
                best_scheme = best_neighbour_scheme
                best_score  = best_neighbour_scheme.score
                start_description = best_neighbour_scheme.description           
                if len(set(best_neighbour_scheme.description)) == 1: #then it's the scheme with everything equal, so quit
                    break
                step += 1
                        
            else:
                break
        
        return best_scheme


    def do_analysis(self):
        models = self.cfg.models #remember the models
        model_selection = self.cfg.model_selection
        partnum = len(self.cfg.partitions)
        self.total_scheme_num = submodels.count_all_schemes(partnum)
        self.total_subset_num = submodels.count_all_subsets(partnum)

        #clear any schemes that are currently loaded
        # TODO Not sure we need this...
        self.cfg.schemes.clear_schemes()        
                
        #first we get a quick and dirty scheme using a forwards search the simplest model
        self.cfg.models = ["LG+G"]
        start_scheme = self.do_forwards_analysis()
        
        #now we use the neighbour algorithm to look around from the start scheme
        self.cfg.models = models #reset to original model set
        best_scheme = self.do_neighbour_analysis(start_scheme)
        
        self.best_result = best_scheme.result               


    def report(self):
        txt = "Best scheme according to Greedy algorithm, analysed with %s"
        best = [(txt % self.cfg.model_selection, self.best_result)]
        self.rpt.write_best_schemes(best)
        self.rpt.write_all_schemes(self.results)

def choose_method(search):
    if search == 'all':
        method = AllAnalysis
    elif search == 'user':
        method = UserAnalysis
    elif search == 'greedy':
        method = GreedyAnalysis
    else:
        log.error("Search algorithm '%s' is not yet implemented", search)
        raise AnalysisError
    return method

