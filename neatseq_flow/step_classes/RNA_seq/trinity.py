""" 
A class that defines a module for RNA_seq assembly using the `Trinity assembler`_.

.. _Trinity assembler: https://github.com/trinityrnaseq/trinityrnaseq/wiki
 
Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    * ``fastq`` files in at least one of the following slots:
        
        * ``sample_data[<sample>]["fastqc"]["readsF"]``
        * ``sample_data[<sample>]["fastqc"]["readsR"]``
        * ``sample_data[<sample>]["fastqc"]["readsS"]``

    
Output:
~~~~~~~~~~~~~

    * puts ``fasta`` output files in the following slots:
        
        * for sample-wise assembly:
        
            * ``sample_data[<sample>]["fasta"]["nucl"]``
            * ``sample_data[<sample>]["assembly"]["trinity_assembl"]["contigs"]``
        
        * for project-wise assembly:
        
            * ``sample_data["fasta"]["nucl"]``
            * ``sample_data["assembly"]["trinity_assembl"]["contigs"]``

                
Parameters that can be set        
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"

    "scope", "sample|project", "Set if project-wide fasta slot should be used"
    
    
Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    trinity1:
        module:     trinity
        base:       trin_tags1
        script_path: /path/to/Trinity
        qsub_params:
            node:      sge213
            -pe:       shared 20
        redirects:
            --grid_conf:        /path/to/SGE_Trinity_conf.txt
            --CPU:              20
            --seqType:          fq
            --JM:               140G
            --min_kmer_cov:     2
            --full_cleanup:



"""



import os
import sys
import re
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.0.1"
class Step_trinity(Step):
    
    def step_specific_init(self):
        self.shell = "csh"      # Can be set to "bash" by inheriting instances
        self.file_tag = ".Trinity.fasta"
        
        
        
    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
            Here you should do testing for dependency output. These will NOT exist at initiation of this instance. They are set only following sample_data updating
        """
        
        
        # Assert that all samples have reads files:
        for sample in self.sample_data["samples"]:    
            if not {"readsF", "readsR", "readsS"} & set(self.sample_data[sample]["fastq"].keys()):
                raise AssertionExcept("No read files\n",sample)
         
        if "scope" in self.params:
          
            if self.params["scope"]=="project":
                # Prepare "fasta" slot for output
                if "fasta" not in self.sample_data.keys():
                    self.sample_data["fasta"] = dict()
                if "assembly" not in self.sample_data.keys():
                    self.sample_data["assembly"] = dict()
                    self.sample_data["assembly"][self.step] = dict()
                    

            elif self.params["scope"]=="sample":
                
                for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
                    # Making sure each sample has an "assembly" slot to store contigs and scaffolds
                    if "assembly" not in self.sample_data[sample]:
                        self.sample_data[sample]["assembly"] = {}
                    if self.step not in self.sample_data[sample]["assembly"]:
                        self.sample_data[sample]["assembly"][self.step] = {}

                    # Making sure a "fasta" slot exists to store contigs:
                    if "fasta" not in self.sample_data[sample]:
                        self.sample_data[sample]["fasta"] = {}
            else:
                raise AssertionExcept("'scope' must be either 'sample' or 'project'")
        else:
            raise AssertionExcept("No 'scope' specified.")
        
        
        ##########################
        

            
        pass     

        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        
        pass

    def build_scripts(self):
    
        if self.params["scope"] == "project":
            self.build_scripts_project()
        else:
            self.build_scripts_sample()
            
            
    def build_scripts_project(self):
        
        
        # Name of specific script:
        self.spec_script_name = "_".join([self.step,self.name,self.sample_data["Title"]])

        self.script = ""

        # This line should be left before every new script. It sees to local issues.
        # Use the dir it returns as the base_dir for this step.
        use_dir = self.local_start(self.base_dir)

        forward = list()   # List of all forward files
        reverse = list()   # List of all reverse files
        single = list()    # List of all single files
        
        # Loop over samples and concatenate read files to $forward and $reverse respectively
        # add cheack if paiered or single !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash
            # If both F and R reads exist, adding them to forward and reverse
            # Assuming upstream input testing to check that if there are F reads then there are also R reads.
            if "readsF" in self.sample_data[sample]["fastq"].keys():
                forward.append(self.sample_data[sample]["fastq"]["readsF"])
                reverse.append(self.sample_data[sample]["fastq"]["readsR"])
            if "readsS" in self.sample_data[sample]["fastq"].keys():
                single.append(self.sample_data[sample]["fastq"]["readsS"])

        # Concatenate all filenames separated by commas:
        single  = ",".join(single)   if (len(single) > 0) else None
        forward = ",".join(forward)  if (len(forward) > 0) else None
        reverse = ",".join(reverse)  if (len(reverse) > 0) else None

        # Adding single reads to end of left (=forward) reads
        if single != None and forward != None:
            forward = ",".join([forward,single])

        self.script += self.get_script_const()

        # The results will be put in data/step_name/name/Title
        self.script += "--output %s \\\n\t" % os.sep.join([use_dir, self.sample_data["Title"]])
            
        #add if single or paired!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if (forward): 
            self.script += "--left %s \\\n\t" % forward
            self.script += "--right %s \n\n" % reverse
        elif (single):
            self.script += "--single %s \n\n" % single
        
        
        # Store results to fasta and assembly slots:
        self.sample_data["fasta"]["nucl"] = "%s%s%s%s" % (self.base_dir, os.sep, self.sample_data["Title"], self.file_tag)
        self.sample_data["assembly"][self.step]["contigs"] = "%s%s%s%s" % (self.base_dir, os.sep, self.sample_data["Title"], self.file_tag)
        
        self.stamp_file(self.sample_data["assembly"][self.step]["contigs"])

       
        # Move all files from temporary local dir to permanent base_dir
        self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)
     
            
        
        
        self.create_low_level_script()
                    
#################################################
    def build_scripts_sample(self):
        
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

        # Name of specific script:
            self.spec_script_name = "_".join([self.step,self.name,sample])
            self.script = ""


            # Make a dir for the current sample:
            sample_dir = self.make_folder_for_sample(sample)
            
            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(sample_dir)

            self.script += self.get_script_const()

            self.script += "--output %s \\\n\t" % use_dir
            
            if "readsF" in self.sample_data[sample]["fastq"].keys():
                self.script += "--left %s \\\n\t" % self.sample_data[sample]["fastq"]["readsF"]
                self.script += "--right %s \\\n\t" % self.sample_data[sample]["fastq"]["readsR"]
            if "readsS" in self.sample_data[sample]["fastq"].keys():
                self.script += "--single %s \n\n" % self.sample_data[sample]["fastq"]["readsS"]

            # If there is an extra "\\\n\t" at the end of the script, remove it.
            self.script = self.script.rstrip("\\\n\t") + "\n\n"

            # Store results to fasta and assembly slots:
            self.sample_data[sample]["fasta"]["nucl"] = sample_dir + "Trinity.fasta"
            self.sample_data[sample]["assembly"][self.step]["contigs"] = sample_dir + "Trinity.fasta"

            self.stamp_file(self.sample_data[sample]["assembly"][self.step]["contigs"])

                
            # Wrapping up function. Leave these lines at the end of every iteration:
            self.local_finish(use_dir,sample_dir)       # Sees to copying local files to final destination (and other stuff)

            self.create_low_level_script()
                        
            
            
                 
            
     