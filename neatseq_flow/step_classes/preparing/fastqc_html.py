

""" A module for running fastqc. 

Creates scripts that run fastqc on all available fastq files.

Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
* fastq files in one of the following slots:

    * ``sample_data[<sample>]["fastqc"]["readsF"]``
    * ``sample_data[<sample>]["fastqc"]["readsR"]``
    * ``sample_data[<sample>]["fastqc"]["readsS"]``

Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
* puts fastqc output files in the following slots:
        
    * ``sample_data[<sample>]["fastq"]["fastqc"]["readsF"|"readsR"|"readsS"]["html"|"zip"]``
            
 

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


::

    fqc_merge1:
        module: fastqc_html
        base: merge1
        script_path: /path/to/FastQC/fastqc
        qsub_params:
            -pe: shared 15
        redirects:
            --threads: 15

 

"""

import os
import sys
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.0.1"
class Step_fastqc_html(Step):

    def step_specific_init(self):
        self.shell = "csh"      # Can be set to "bash" by inheriting instances
        self.file_tag = "fasqc"

    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """
        
        
        # Assert that all samples have reads files:
        for sample in self.sample_data["samples"]:    
            if not "fastq" in self.sample_data[sample]:
                raise AssertionExcept("No fastq files defined.\n", sample)
            if not {"readsF", "readsR", "readsS"} & set(self.sample_data[sample]["fastq"].keys()):
                raise AssertionExcept("No read files defined\n", sample)

        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        if "sum_script" in self.params.keys():
            self.script = "%(script)s \\\n\t-d %(indir)s \\\n\t-o %(outdir)s\n\n" % \
                    {"script" : self.params["sum_script"],                          \
                     "indir"  : self.base_dir,                                      \
                     "outdir" : self.base_dir}

        
    
    def build_scripts(self):
        """ This is the actual script building function
            Most, if not all, editing should be done here 
            HOWEVER, DON'T FORGET TO CHANGE THE CLASS NAME AND THE FILENAME!
        """
        
        
        # Each iteration must define the following class variables:
            # spec_script_name
            # script
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

            # Name of specific script:
            self.spec_script_name = "_".join([self.step,self.name,sample])
            self.script = ""
            
            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(self.base_dir)
            
            
            self.script += self.get_script_const()

            self.script += "--outdir " + use_dir
            # Create temporary dict to store the output file names:
            temp_dict = {}
            for direction in ("readsF","readsR","readsS"):
                if direction in self.sample_data[sample]["fastq"].keys():
                    self.script += " \\\n\t" + self.sample_data[sample]["fastq"][direction] 
            self.script += "\n\n";
            
            
            for direction in ("readsF","readsR","readsS"):
                if direction in self.sample_data[sample]["fastq"].keys():
                    temp_dict[direction] = {}
                    file_basename = os.path.basename(self.sample_data[sample]["fastq"][direction])
                    temp_dict[direction]["html"] = self.base_dir + file_basename + "_fastqc.html"
                    temp_dict[direction]["zip"] = self.base_dir + file_basename + "_fastqc.zip"

            
            # Move all files from temporary local dir to permanent base_dir
            self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)

            self.sample_data[sample]["fastq"]["fastqc"] = temp_dict
            
                    
            
            self.create_low_level_script()
                    
