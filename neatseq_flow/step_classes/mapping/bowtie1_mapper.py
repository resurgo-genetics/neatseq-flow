

""" A module for running bowtie1 mapper:

The reads stored in each sample are aligned to one of the following bowtie indices:

* An external index passed with the ``ebwt`` parameter.
* A bowtie index on a project fasta files, such as an assembly from all samples. Specify with ``bowtie1_mapper:scope  project``
* A sample bowtie1 index on a sample-specific fasta file, such as from a sample-wise assembly or from the sample file. Specify with ``bowtie1_mapper:scope  sample``

The latter two options **must** come after a ``bowtie1_builder`` instance.


Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* fastq files in one of the following slots:

    * ``sample_data[<sample>]["fastqc"]["readsF"]``
    * ``sample_data[<sample>]["fastqc"]["readsR"]``
    * ``sample_data[<sample>]["fastqc"]["readsS"]``
    

Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* Puts output sam files in the following slots:
    ``self.sample_data[<sample>]["fastq"]["mapping"]["sam"]``

* Puts the name of the mapper in:
    ``self.sample_data[<sample>]["fastq"]["mapping"]["mapper"]``

* Puts fasta of reference genome (if one is given in param file) in:
    ``self.sample_data[<sample>]["fastq"]["mapping"]["reference"]``

Parameters that can be set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 15, 10, 10

    "ebwt", "path to bowtie1 index", "If not given, will look for a project bowtie1 index and then for a sample bowtie1 index"
    "ref_genome", "path to genome fasta", "If ebwt is NOT given, will use the equivalent internal fasta. If ebwt IS given, and ref_genome is NOT passed, will leave the reference slot empty."
    "scope", "project | sample", "Indicates whether to use a project or sample bowtie1 index."

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**For external index:**

::

    bwt1:
        module: bowtie1_mapper
        base: trim1
        script_path: /path/to/bowtie
        qsub_params:
            -pe: shared 20
        ebwt: /path/to/bowtie1_index/ref_genome
        ref_genome: /path/to/ref_genome.fna
        redirects:
            -p: 20

**For project bowtie index:**

::

    bwt1_1:
        module: bowtie1_mapper
        base: bwt1_bld_ind
        script_path: /path/to/bowtie
        scope: project

"""


import os
import sys
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.0.1"
class Step_bowtie1_mapper(Step):
    
    def step_specific_init(self):
        self.shell = "bash"      # Can be set to "bash" by inheriting instances
        self.file_tag = "bowtie1_mapper"

    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """
        
        # Initializing a "mapping" dict for each sample:
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

            try:
                self.sample_data[sample]["fastq"]["mapping"]
            except KeyError:
                self.sample_data[sample]["fastq"]["mapping"] = {}
            else:
                self.write_warning("mapping dict exists for sample. Double mapping steps?\n", sample)

        # Require either 'scope' or 'ebwt':
        if "scope" in self.params:
            # If scope defined, comment if also ebwt exists.
            if "ebwt" in self.params.keys():
                raise AssertionExcept("Both 'scope' and 'ebwt' specified!\n")

            try:
                # Loop over samples to set the reference genome:
                for sample in self.sample_data["samples"]:
                    if self.params["scope"] == "project":
                        # Set project wide reference:
                        self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.sample_data["bowtie1"]["fasta"]
                    elif self.params["scope"] == "sample":
                        # Set per-sample reference:
                        self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.sample_data[sample]["bowtie1"]["fasta"]
                    else:
                        raise AssertionExcept("Scope must be either 'sample' or 'project'\n" )
                
            except KeyError:
                raise AssertionExcept("There is a mismatch between 'scope' and the existing bowtie1 index for sample\n", sample)
                
                  
            if "ref_genome" in self.params.keys():
                self.write_warning("ref_genome was passed, and 'scope' was defined. Ignoring ref_genome\n")
        else:
            # If scope is not defined, require '-x'
            if not "ebwt" in self.params.keys():
                raise AssertionExcept("Neither 'scope' nor 'ebwt' specified.\n")

        
            # Storing reference genome for use by downstream steps:
            if "ref_genome" in self.params.keys():
                for sample in self.sample_data["samples"]:
                    # If reference already exists, ignore ref_genome
                    if "reference" in self.sample_data[sample]["fastq"]["mapping"]:
                        self.write_warning("ref_genome was passed, but a reference already exists. Setting reference to 'ref_genome'\n")
                
                    self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.params["ref_genome"]
            else:
                self.write_warning("No reference given. It is highly recommended to give one!\n")
                
                




        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        pass
        
    
    def build_scripts(self):
        """ This is the actual script building function
            Most, if not all, editing should be done here 
            HOWEVER, DON'T FORGET TO CHANGE THE CLASS NAME AND THE FILENAME!
        """
        
        
        # Each iteration must define the following class variables:
            # self.spec_script_name
            # self.script
        
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

            # Make a dir for the current sample:
            sample_dir = self.make_folder_for_sample(sample)

            # Name of specific script:
            self.spec_script_name = "_".join([self.step,self.name,sample])
            self.script = ""
            
            
            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(sample_dir)
 
            # Define location and prefix for output files:
            output_prefix = "%s_%s" % (sample, self.name)
            output_prefix = use_dir + output_prefix
            

            # Set output to sam even if not specified by user:
            if "-S" not in self.params["redir_params"]:
                self.params["redir_params"]["--sam"] = None

            # Get constant part of script:
            self.script += self.get_script_const()
            
            

            # self.script += "--rg-id %s \\\n\t" % sample
            self.script += "--sam-RG   SM:%s \\\n\t" % sample
            
            
            # If reference index not defined by user with "ebwt", use bowtie index in sample_data.
            #    Id that dosent exist either, throw up and balk away:
            try:  # If scope was passed, include either project or sample bowtie2 index
                if self.params["scope"] == "project":
                    self.script += "%s \\\n\t" % self.sample_data["bowtie1"]["index"]
                else:
                    self.script += "%s \\\n\t" % self.sample_data[sample]["bowtie1"]["index"]
            except KeyError:  # Otherwise do nothing - '-x' is included through redirect params
                self.script += "%s \\\n\t" % self.params["ebwt"]

            # if "ebwt" in self.params.keys():
                # self.script += "%s \\\n\t" % self.params["ebwt"]
            # else:
                # if "bowtie1" in self.sample_data.keys():  # A bowtie1 index has been created in self.sample_data["bowtie1"]
                    # self.script += "%s \\\n\t" % self.sample_data["bowtie1"]["index"]
                    # self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.sample_data["bowtie1"]["fasta"]
                # elif "bowtie1" in self.sample_data[sample]:  # A bowtie1 index has been created in self.sample_data[sample]["bowtie1"]
                    # self.script += "%s \\\n\t" % self.sample_data[sample]["bowtie1"]["index"]
                    # self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.sample_data[sample]["bowtie1"]["fasta"]
                # else:
                    # raise AssertionExcept("In %s: Sample %s does not have a reference defined, nor did you pass one with 'ebwt' parameter...\n" % (self.name, sample))

                    
            # assert set("readsF","readsR","readsS") & self.sample_data["sample"].keys(), "There are no reads for sample %s" % sample
            if "readsF" in self.sample_data[sample]["fastq"].keys():
                self.script += "-1 %s \\\n\t-2 %s\\\n\t" % (self.sample_data[sample]["fastq"]["readsF"],self.sample_data[sample]["fastq"]["readsR"])
            if "readsS" in self.sample_data[sample]["fastq"].keys():
                self.script += "%s \\\n\t" % self.sample_data[sample]["fastq"]["readsS"]

            self.script += "%s.sam \n\n" % output_prefix


            self.sample_data[sample]["fastq"]["mapping"]["sam"] = "%s.sam" % output_prefix
            self.stamp_file(self.sample_data[sample]["fastq"]["mapping"]["sam"])
            
            # Storing name of mapper. might be useful:
            self.sample_data[sample]["fastq"]["mapping"]["mapper"] = self.get_step_step()  
            
            # Storing reference genome for use by downstream steps:
            if "ref_genome" in self.params.keys():
                # If reference already exists, ignore ref_genome
                if "reference" in self.sample_data[sample]["fastq"]["mapping"]:
                    self.write_warning("ref_genome was passed, but no bowtie1 index was given with 'ebwt'.\n\tIgnoring ref_genome and using the following fasta file instead:\n\t%s" % self.sample_data[sample]["fastq"]["mapping"]["reference"])
                    
                else:
                    self.sample_data[sample]["fastq"]["mapping"]["reference"] = self.params["ref_genome"]
            else:
                self.write_warning("No reference given. It is highly recommended to give one!\n")
        
        
            # Move all files from temporary local dir to permanent base_dir
            self.local_finish(use_dir,self.base_dir)       # Sees to copying local files to final destination (and other stuff)
       
            
            
            self.create_low_level_script()
                    
