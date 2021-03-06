import luigi
import os
import time
import subprocess
import pandas as pd
from luigi import Parameter
from tasks.rnaSeq.align_rnaseq_reads_with_genome import alignReads
from tasks.assembly.kmergenie import kmergenie_formater_bbduk
from tasks.assembly.kmergenie import kmergenie_formater_reformat
from tasks.assembly.kmergenie import optimal_kmer
from tasks.readCleaning.preProcessReads import bbduk
from tasks.readCleaning.preProcessReads import filtlong
from tasks.readCleaning.reFormatReads import reformat
from tasks.rnaSeq.align_rnaseq_reads_with_genome_gg_trinity import mapReadsToGenomeGG


def run_cmd(cmd):
	p = subprocess.Popen(cmd, bufsize=-1,
						 shell=True,
						 universal_newlines=True,
						 stdout=subprocess.PIPE,
						 executable='/bin/bash')
	output = p.communicate()[0]
	return output

######################################
#Function to prepare Trinity paired-end input
def prepare_trinity_pe_bbduk(input_file):
	with open(input_file) as ifh:
		sample_name_list = ifh.read().splitlines()
		left_read_name_suffix = '_R1.fastq'
		right_read_name_suffix = '_R2.fastq'
		read_folder = os.path.join(os.getcwd(), "CleanedReads", "Cleaned_PE_Reads" + "/")
		left_read_name_list = [ read_folder + x + left_read_name_suffix for x in sample_name_list]
		right_read_name_list =[ read_folder + x + right_read_name_suffix for x in sample_name_list]

		left_reads = ','.join(left_read_name_list)
		right_reads = ','.join(right_read_name_list)

		Trinity_PE_Input = "--left " + left_reads + " --right " + right_reads
		return Trinity_PE_Input

#Function to prepare Trinity Single-end input
def prepare_trinity_se_bbduk(input_file):
	with open(input_file) as ifh:
		sample_name_list = ifh.read().splitlines()
		read_name_suffix = '.fastq'
		read_folder = os.path.join(os.getcwd(), "CleanedReads", "Cleaned_SE_Reads" + "/")
		read_name_list = [ read_folder + x + read_name_suffix for x in sample_name_list]
		reads = ','.join(read_name_list)
		Trinity_SE_Input = "--single" + reads + " "
		return Trinity_SE_Input
######################################
def prepare_trinity_pe_reformat(input_file):
	with open(input_file) as ifh:
		sample_name_list = ifh.read().splitlines()
		left_read_name_suffix = '_R1.fastq'
		right_read_name_suffix = '_R2.fastq'
		read_folder = os.path.join(os.getcwd(), "VerifiedReads", "Verified_PE_Reads" + "/")
		left_read_name_list = [ read_folder + x + left_read_name_suffix for x in sample_name_list]
		right_read_name_list =[ read_folder + x + right_read_name_suffix for x in sample_name_list]
		left_reads = ','.join(left_read_name_list)
		right_reads = ','.join(right_read_name_list)
		Trinity_PE_Input = "--left " + left_reads + " --right " + right_reads
		return Trinity_PE_Input

#Function to prepare Trinity Single-end input
def prepare_trinity_se_reformat(input_file):
	with open(input_file) as ifh:
		sample_name_list = ifh.read().splitlines()
		read_name_suffix = '.fastq'
		read_folder = os.path.join(os.getcwd(), "VerifiedReads", "Verified_SE_Reads" + "/")
		read_name_list = [ read_folder + x + read_name_suffix for x in sample_name_list]
		reads = ','.join(read_name_list)
		Trinity_SE_Input = "--single" + reads + " "
		return Trinity_SE_Input
############################################
class GlobalParameter(luigi.Config):
	genome_suffix=luigi.Parameter()
	read_library_type=luigi.Parameter()
	organism_domain=luigi.Parameter()
	genome_name=luigi.Parameter()
	genome_dir=luigi.Parameter()
	transcriptome_dir=luigi.Parameter()
	threads = luigi.Parameter()
	maxMemory = luigi.Parameter()
	feature_type=luigi.Parameter()
	adapter=luigi.Parameter()


class ggTrinity(luigi.Task):

	project_name=luigi.Parameter(default="RNASeqAnalysis")
	adapter = GlobalParameter().adapter
	read_library_type = GlobalParameter().read_library_type
	organism_domain = GlobalParameter().organism_domain
	threads = GlobalParameter().threads
	pre_process_reads = luigi.ChoiceParameter(choices=["yes", "no"], var_type=str)
	genome_name=GlobalParameter().genome_name
	rnaseq_aligner = luigi.ChoiceParameter(choices=["subread","star","hisat2","dart", "segemehl","bowtie2"],var_type=str)
	annotation_file_type = luigi.ChoiceParameter(choices=["GFF", "GTF"], var_type=str)

	maxMemory = luigi.Parameter(description="Maximum Memory in GB",default="20")
	maxIntron = luigi.Parameter(description="Maximum Intron Length",default="2000")
	minContigLength = luigi.Parameter(description="Minimum Contig Length",default="200")
	threads = luigi.Parameter(description="Number of threads to be used", default="20")



	def requires(self):

		if self.read_library_type == "pe":
			return [mapReadsToGenomeGG(project_name=self.project_name,pre_process_reads=self.pre_process_reads,
									   annotation_file_type=self.annotation_file_type,
									   rnaseq_aligner=self.rnaseq_aligner)]

		if self.read_library_type == "se":
			return [mapReadsToGenomeGG(project_name=self.project_name,pre_process_reads=self.pre_process_reads,
									   annotation_file_type=self.annotation_file_type,
									   rnaseq_aligner=self.rnaseq_aligner)]


#Trinity --genome_guided_bam hexcentricum.bam --genome_guided_max_intron 10000 --max_memory 20G --CPU 10



	def output(self):
		gg_assembled_transcript_folder = os.path.join(os.getcwd(), self.project_name, "genomeguided_assembly","trinity_" + self.rnaseq_aligner +"_" + self.read_library_type + "/")

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "star", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "star", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "star", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "star", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "subread", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "subread", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "subread", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "subread", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		# HISAT2 OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "hisat2", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "hisat2", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "hisat2", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "hisat2", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		# BOWTIE2 OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "bowtie2", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "bowtie2", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		# DART OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "dart", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "dart", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "dart", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "dart", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		# SEGEMEHL OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "segemehl", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "segemehl", self.organism_domain == "prokaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "segemehl", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

		if all([self.read_library_type == "se", self.rnaseq_aligner == "segemehl", self.organism_domain == "eukaryote"]):
			return {'out1': luigi.LocalTarget(gg_assembled_transcript_folder + "/" + "Trinity-GG.fasta")}

	def run(self):
		mapFolder = os.path.join(os.getcwd(), self.project_name,"rnaseq_genome_alignment",self.genome_name +"_"+self.rnaseq_aligner+"_"+self.read_library_type+"_map"+ "/")
		gg_assembled_transcript_folder = os.path.join(os.getcwd(), self.project_name, "genomeguided_assembly","trinity_" + self.rnaseq_aligner +"_" + self.read_library_type + "/")
		gg_transcript_index_folder = os.path.join(os.getcwd(), self.project_name,"rnaseq_genome_alignment",self.genome_name+"_bowtie2_"+self.read_library_type+"_index"+ "/")

		cmd_run_trinity_pe = "[ -d  {gg_assembled_transcript_folder} ] || mkdir -p {gg_assembled_transcript_folder}; " \
							 "Trinity " \
							 "--min_contig_length {minContigLength} " \
							 "--max_memory {maxMemory}G " \
							 "--genome_guided_bam {mapFolder}{genome_name}.bam " \
							 "--genome_guided_max_intron {maxIntron} " \
							 "--output {gg_assembled_transcript_folder} " \
							 "--CPU {threads} " \
							 "--include_supertranscripts " \
							 "--full_cleanup " \
			.format(gg_assembled_transcript_folder=gg_assembled_transcript_folder,
					mapFolder=mapFolder,
					minContigLength=self.minContigLength,
					maxMemory=self.maxMemory,
					genome_name=self.genome_name,
					maxIntron=self.maxIntron,
					threads=self.threads)

		cmd_run_trinity_se = "[ -d  {gg_assembled_transcript_folder} ] || mkdir -p {gg_assembled_transcript_folder}; " \
							 "Trinity " \
							 "--min_contig_length {minContigLength} " \
							 "--max_memory {maxMemory}G " \
							 "--genome_guided_bam {mapFolder}{genome_name}.bam " \
							 "--genome_guided_max_intron {maxIntron} " \
							 "--output {gg_assembled_transcript_folder} " \
							 "--CPU {threads} " \
							 "--include_supertranscripts " \
							 "--full_cleanup " \
			.format(gg_assembled_transcript_folder=gg_assembled_transcript_folder,
					mapFolder=mapFolder,
					minContigLength=self.minContigLength,
					maxMemory=self.maxMemory,
					genome_name=self.genome_name,
					maxIntron=self.maxIntron,
					threads=self.threads)

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "star", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "star", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "star", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "star", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		# HISAT2 OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "hisat2", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "hisat2", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "hisat2", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "hisat2", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		# BOWTIE2 OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "bowtie2", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "bowtie22", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		# DART OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "dart", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "dart", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "dart", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "dart", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		# SEGEMEHL OUTPUT
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "segemehl", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "segemehl", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "segemehl", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "segemehl", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		#SUBREAD
		if all([self.read_library_type == "pe", self.rnaseq_aligner == "subread", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "subread", self.organism_domain == "prokaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

		if all([self.read_library_type == "pe", self.rnaseq_aligner == "subread", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_pe)
			print(run_cmd(cmd_run_trinity_pe))

		if all([self.read_library_type == "se", self.rnaseq_aligner == "subread", self.organism_domain == "eukaryote"]):
			print("****** NOW RUNNING COMMAND ******: " + cmd_run_trinity_se)
			print(run_cmd(cmd_run_trinity_se))

