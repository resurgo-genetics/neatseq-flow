


""" A module for running macs2 callpeak:


Requires
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* bam files in the following slots:

    * ``sample_data[<sample>]["fastqc"]["mapping"]["bam"]``

* If using control (input) samples, make sure you include a sample-control table in your sample file.

Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Puts output macs2 output files in the following slots:

    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["prefix"])``
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["peak_bed"])``
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["peak_xls"])``
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["summit_bed"])``

* If ``--bdg`` (or ``-B``) was specified, puts output bdg files in the following slots:
            
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["control_lambda"]`` - Control BedGraph
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["treat_pileup"]`` - Treatment BedGraph
    * ``self.sample_data[<sample>]["fastq"]["mapping"]["bdg"]`` - Treatment BedGraph
    * ``self.sample_data[<control>]["fastq"]["mapping"]["bdg"]`` - Control BedGraph
                
* If ``bedToBigBed_path`` was specified, puts output bigbed files in the following slots:
            
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["bb"]``

* If ``getfasta`` was specified, puts output fasta files in the following slots:
            
    * ``self.sample_data[<sample>]["fastq"]["chip_seq"]["peak_fasta"]``

    
Parameters that can be set
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table:: 
    :header: "Parameter", "Values", "Comments"
    :widths: 15, 10, 10

    "bedToBigBed_path", "path to bedToBigBed", "Runs bedToBigBed to convert the peak bed files into bigbed for uploading to UCSC."
    "chrom.sizes", "path to chrom.sizes for reference genome", "If running bedToBigBed, you must supply the genome chrom.sizes file."
    "getfasta", "", "If set, a fasta file containing the peak sequences will be produced."

Lines for parameter file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    macs1_CP:
        module: macs2_callpeak
        base: samtools1
        script_path: /path/to/bin/macs2 callpeak
        bedToBigBed_path: /path/to/kentUtils/bin/bedToBigBed
        chrom.sizes: /path/to/genome.chrom.sizes
        getfasta: /path/to/bedtools getfasta -name -s
        redirects:
            --SPMR: 
            --bdg: 
            -g:     mm
            --bw:   400


"""
import os
import os.path
import sys
from PLC_step import Step,AssertionExcept


__author__ = "Menachem Sklarz"
__version__ = "1.0.1"
class Step_macs2_callpeak(Step):



    def step_specific_init(self):
        self.shell = "bash"      # Can be set to "bash" by inheriting instances
        self.file_tag = "macs2"

    def step_sample_initiation(self):
        """ A place to do initiation stages following setting of sample_data
        """
        
        # Initializing a "mapping" dict for each sample:
        for sample in self.sample_data["samples"]:      # Getting list of samples out of samples_hash

            # Make sure there is a mapping dict
            try:
                self.sample_data[sample]["fastq"]["mapping"]
            except KeyError:
                raise AssertionExcept("Mapping dict does not exist for sample. samtools can not run without a mapping\n", sample)
            # Make sure there is a bam file

            # assert "bam" in self.sample_data[sample]["mapping"].keys(),"Sample %s does not have a bam file!\n" % sample

            try:
                self.sample_data[sample]["fastq"]["mapping"]["bam"]
            except KeyError:
                raise AssertionExcept("Sample does not have a bam file!\n" ,sample)

                
        try:
            self.sample_data["Controls"]
        except KeyError:
            raise AssertionExcept("You must define sample:control pairs\n")
            
        for sample in self.sample_data["Controls"].keys():      # Getting list of samples out of Controls dict.
            # Create "chip_seq" dict for results, if does not exist
            # Only in samples. Not in controls....
            try:
                self.sample_data[sample]["fastq"]["chip_seq"]
            except KeyError:
                self.sample_data[sample]["fastq"]["chip_seq"] = {}
            else:
                self.write_warning("chip_seq dict exists for sample %s. Double peak calling steps?\n", sample)


        pass
        
        

        
    def create_spec_wrapping_up_script(self):
        """ Add stuff to check and agglomerate the output data
        """
        self.make_sample_file_index()   # see definition below
        
    
    def build_scripts(self):
        """ This is the actual script building function
            Most, if not all, editing should be done here 
            HOWEVER, DON'T FORGET TO CHANGE THE CLASS NAME AND THE FILENAME!
        """

        # Each iteration must define the following class variables:
            # self.spec_script_name
            # self.script
        for sample in self.sample_data["Controls"].keys():      # Getting list of samples out of Controls dict.

            # Make a dir for the current sample:
            sample_dir = self.make_folder_for_sample(sample)

            # Name of specific script:
            self.spec_script_name = "_".join([self.step,self.name,sample])
            self.script = ""

            # Name of control sample:
            control = self.sample_data["Controls"][sample]

            # This line should be left before every new script. It sees to local issues.
            # Use the dir it returns as the base_dir for this step.
            use_dir = self.local_start(sample_dir)

            # Defined full path to output filename
            output_filename = "%s.%s" % (sample, self.file_tag)
            
                
                
            self.script += self.get_script_const()
                
            # Add lines for sample mapping files:
            self.script += "-t %s \\\n\t" % self.sample_data[sample]["fastq"]["mapping"]["bam"]
            if not "nocontrol" in self.params.keys():
                self.script += "-c %s \\\n\t" % self.sample_data[control]["fastq"]["mapping"]["bam"]
        
            # Add output directory
            self.script += "--name %s \n\n" % output_filename
            self.script += "--outdir %s \n\n" % use_dir
            
            # Storing the output file in $samples_hash
            self.sample_data[sample]["fastq"]["chip_seq"]["prefix"] = "".join([sample_dir, output_filename])
            self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"] = "".join([sample_dir, output_filename, "_peaks.bed"])
            self.sample_data[sample]["fastq"]["chip_seq"]["peak_xls"] = "".join([sample_dir, output_filename, "_peaks.xls"])
            self.sample_data[sample]["fastq"]["chip_seq"]["summit_bed"] = "".join([sample_dir, output_filename, "_summits.bed"])
            
            self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["prefix"])
            self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"])
            self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["peak_xls"])
            self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["summit_bed"])

            # Storing bedgraph files if should exist:
            
            if "--bdg" in self.params["redir_params"] or "-B" in self.params["redir_params"]:
                self.sample_data[sample]["fastq"]["chip_seq"]["control_lambda"] = "".join([sample_dir, output_filename, "_control_lambda.bdg"])
                self.sample_data[sample]["fastq"]["chip_seq"]["treat_pileup"] = "".join([sample_dir, output_filename, "_treat_pileup.bdg"])
                # Saving the treatment pileup bdg file as the main mapping bdg
                # (saving in mapping because it is a derivation of the mapping data)
                self.sample_data[sample]["fastq"]["mapping"]["bdg"] = "".join([sample_dir, output_filename, "_treat_pileup.bdg"])
                # Saving the control pileup bdg file as the main control bdg
                self.sample_data[control]["fastq"]["mapping"]["bdg"] = "".join([sample_dir, output_filename, "_control_lambda.bdg"])
                # Stamping all bdg files
                self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["control_lambda"])
                self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["treat_pileup"])
            
            ##############################
            # # Add conversion of peak bed to bigbed
            if "bedToBigBed_path" in self.params.keys():
                if not "chrom.sizes" in self.params.keys():
                    raise AssertionExcept("If bedToBigBed_path is passed, you also must sepcify a 'chrom.sizes' path")
                out_bed_filename = "%s.cut.bed" % self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"]
                out_bb_filename = "%s.cut.bb" % self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"]

# Probably better to use the following perl one-liner:
# perl -e 'while($line=<>){$line=~s/((?:\S*\s*){3})\.\d*(\s.*)/$1$2/; print $line}' bed_file                
# This will retain only the int part in column 4 while leaving the rest intact.
                self.script += """

                
                
#### Convert bed to bigbed for UCSC browser



if [ -e %(in_bed)s ] 
then
    # First, removing final column which has a float instead of an integer:
    cat \\
        %(in_bed)s \\
        | cut -f 1-4 \\
        > %(out_bed)s

    # Convert to bb
    %(exec_path)s \\
        %(out_bed)s \\
        %(chrom_sizes)s \\
        %(out_bb)s
fi

                        """ % {"in_bed"      : self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"],   \
                               "exec_path"   : self.params["bedToBigBed_path"],                    \
                               "chrom_sizes" : self.params["chrom.sizes"],                         \
                               "out_bb"      : out_bb_filename,                                    \
                               "out_bed"     : out_bed_filename}
                
                self.sample_data[sample]["fastq"]["chip_seq"]["bb"] = out_bb_filename
                # Stamping bb file
                self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["bb"])
                
            ##############################
            # # Add extration of peak fasta sequences
            if "getfasta" in self.params.keys():
                try:
                    self.sample_data[sample]["fastq"]["mapping"]["reference"]
                except KeyError:
                    self.write_warning("In %s: No reference exists, but you asked for a fasta file for the peaks. \n\tIn order to get the file you have to set a reference genome in the mapping step (Bowtie in particular)\n")

              
                else:
                
                    self.script += """
# Extract peaks from BED file to fasta file:

if [ -e %(peaks)s ] 
then
    %(exec_path)s
        -fi %(ref_fasta)s \\
        -bed %(bed_file)s  > %(bed_file)s.fasta
fi

                        """ % {"peaks" :     self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"],          \
                               "exec_path" : self.params["getfasta"],                                   \
                               "ref_fasta" : self.sample_data[sample]["fastq"]["mapping"]["reference"], \
                               "bed_file"  : self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"]}
           
                self.sample_data[sample]["fastq"]["chip_seq"]["peak_fasta"] = "%s.fasta" % self.sample_data[sample]["fastq"]["chip_seq"]["peak_bed"]
                # Stamping bb file
                self.stamp_file(self.sample_data[sample]["fastq"]["chip_seq"]["peak_fasta"])

        
        
            # Wrapping up function. Leave these lines at the end of every iteration:
            self.local_finish(use_dir,sample_dir)       # Sees to copying local files to final destination (and other stuff)

            
            self.create_low_level_script()
                    
   
    def make_sample_file_index(self):
        """ Make file containing samples and target file names.
            This can be used by scripts called by create_spec_wrapping_up_script() to summarize the BLAST outputs.
        """
        
        with open(self.base_dir + "DiffBind_files_index.txt", "w") as index_fh:
            index_fh.write("SampleID,bamReads,ControlID,bamControl,Peaks,PeakCaller\n")

            for sample in self.sample_data["Controls"].keys():      # Getting list of samples out of Controls dict.
                control = self.sample_data["Controls"][sample]
                index_fh.write("%s,%s,%s,%s,%s,%s\n" % (sample,\
                                    self.sample_data[sample]["fastq"]["mapping"]["bam"],\
                                    control,\
                                    self.sample_data[control]["fastq"]["mapping"]["bam"],\
                                    self.sample_data[sample]["fastq"]["chip_seq"]["peak_xls"],\
                                    "macs"))
                                    
        self.sample_data["DiffBind_files_index"] = self.base_dir + "DiffBind_files_index.txt"
        
