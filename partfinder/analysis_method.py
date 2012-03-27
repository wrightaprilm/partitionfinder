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

    def do_forwards_analysis(self):
        '''A greedy algorithm for heuristic partitioning searches
        This one does a quick pass using just HKY+G model to get an OK starting scheme
        '''
        log.info("Looking for a starting scheme")
        model_selection = self.cfg.model_selection
        partnum = len(self.cfg.partitions)
        models = self.cfg.models

        #start with the most partitioned scheme
        start_description = range(len(self.cfg.partitions))
        start_scheme = scheme.create_scheme(self.cfg, 1, start_description)
        log.info("Analysing fully partitioned scheme")
        result = self.analyse_scheme(start_scheme, models)
        
        def get_score(my_result):
            #TODO: this is bad. Should use self.cfg.model_selection, or write
            #a new model_selection for scheme.py
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

        best_result = result
        best_score  = get_score(result)
                         
        step = 1
        cur_s = 2

        #now we try out all lumpings of the current scheme, to see if we can find a better one
        #and if we do, we just keep going
        while True:
            log.info("***Starting scheme search step %s***" % step)
            #get a list of all possible lumpings of the best_scheme
            lumpings = algorithm.get_neighbours(start_description)

            best_lumping_score = None
            for lumped_description in lumpings:

                lumped_scheme = scheme.create_scheme(self.cfg, cur_s, lumped_description)
                cur_s += 1
                result = self.analyse_scheme(lumped_scheme, models)
                new_score = get_score(result)

                if best_lumping_score==None or new_score < best_lumping_score:
                    best_lumping_score  = new_score
                    best_lumping_result = result
                    best_lumping_scheme = lumped_scheme
                    best_lumping_desc   = lumped_description

            if best_lumping_score < best_score:
                best_scheme = best_lumping_scheme
                best_score  = best_lumping_score
                best_result = best_lumping_result
                start_description = best_lumping_desc               
                if len(set(best_lumping_desc)) == 1: #then it's the scheme with everything equal, so quit
                    break
                step += 1

            else:
                break

        log.info("Starting Scheme: %s" % best_scheme)

        return best_scheme, start_description

    def do_neighbour_analysis(self, start_description, start_scheme):
        '''A greedy algorithm for heuristic partitioning searches'''
        models = self.cfg.models        
        model_selection = self.cfg.model_selection
        partnum = len(self.cfg.partitions)
        self.cfg.schemes.clear_schemes()        
  
        log.info("***Beginning Neighbour Analysis***")
        log.info("Analysing start scheme with all models")
        print models
        result = self.analyse_scheme(start_scheme, models)
                
        def get_score(my_result):
            #TODO: this is bad. Should use self.cfg.model_selection, or write
            #a new model_selection for scheme.py
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

        best_result = result
        best_score  = get_score(result)
        log.info("Starting scheme has score: %.3f" % best_score)
                         
        step = 1
        cur_s = 2

        #now we try out all lumpings of the current scheme, to see if we can find a better one
        #and if we do, we just keep going
        while True:
            log.info("***Neighbour algorithm step %d***" % step)

            #get a list of all possible lumpings of the best_scheme
            lumpings = algorithm.get_neighbours(start_description)

            best_lumping_score = None
            for lumped_description in lumpings:

                lumped_scheme = scheme.create_scheme(self.cfg, cur_s, lumped_description)
                cur_s += 1
                result = self.analyse_scheme(lumped_scheme, models)
                new_score = get_score(result)

                if best_lumping_score==None or new_score < best_lumping_score:
                    best_lumping_score  = new_score
                    best_lumping_result = result
                    best_lumping_scheme = lumped_scheme
                    best_lumping_desc   = lumped_description

            log.info("Best scheme: %s" % best_lumping_scheme.name)
            log.info("Best score: %.3f" % best_lumping_score)

            if best_lumping_score < best_score:
                best_scheme = best_lumping_scheme
                best_score  = best_lumping_score
                best_result = best_lumping_result
                start_description = best_lumping_desc               
                if len(set(best_lumping_desc)) == 1: #then it's the scheme with everything equal, so quit
                    break
                step += 1
                        
            else:
                break
        
        return best_scheme, start_description, best_result, best_score


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
        start_scheme, start_description = self.do_forwards_analysis()
        
        #now we do sequential passes of the neighbour algorithm

        self.cfg.schemes.clear_schemes()
        self.schemes_analysed = 0
        #self.cfg.models = models #now we go with all possible models
        best_scheme, start_description, best_result, best_score = self.do_neighbour_analysis(start_description, start_scheme)

        self.best_result = best_result                


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

