#!/usr/bin/env ruby 
#require 'debugger'
require 'optparse'

class ABINIT_Diff
	def initialize(key_words, precision)
		@key_words = key_words
		@precision = precision
		@numeric_re = /(?:-)?\b\d+(?:\.\d+)?(?:e\+\d+|e-\d+|E\+\d+|E-\d+)?\b/
		digits_after = (precision > 6) ? 6 : precision
		@format = "%.#{digits_after}E"
		#before -> before ABINIT calculation < = > echo of the input variables
		@before_re = /echo values of preprocessed input variables.*?$(.+?)=/m
		#after -> after ABINIT calculation < = > output
		@after_re = /echo values of variables after computation.*?$(.+?)=/m
	end

	def show(files)
		if files.size == 1
			show_single_file(files.first[:text])
		else
			show_multiple_files(files)
		end
	end

	protected

	def show_multiple_files(files)
		file_to_params = Hash[files.map{ |f| [f[:name], find_ab_params(f[:text], @after_re)]}]
		@key_words.each do |key_word|
			puts ""
			file_to_params.each do |file_name, params|
				puts "#{key_word} #{file_name}"
				puts params[key_word]
			end
		end
	end

	def show_single_file(text)
		before_params = find_ab_params(text, @before_re)
		after_params = find_ab_params(text, @after_re)

		@key_words.each do |key_word|
			puts ""
			puts "#{key_word} before:"
			puts before_params[key_word]
			puts "#{key_word} after:"
			puts after_params[key_word]
		end
	end

	def find_ab_params(text, calc_text_re)
		calc_text = calc_text_re.match(text).captures[0]
		params = {}
		@key_words.each do |key_word|
			params[key_word] = get_values(calc_text, key_word)
		end
		params
	end

	def get_values(calc_text, key_word)
		values_re = /#{key_word}((\s*?#{@numeric_re}\s*?)+)/m
		m = values_re.match(calc_text)
		(m.nil?) ? "none" : format_values(m.captures[0])
	end

	def format_values(values_str)
		def format_value(num_str)
			num = num_str.to_f.round(@precision)

			formatted = @format % num
			#num = formatted.to_f
			#for indentation purposes
			(formatted.split('')[0] == "-") ? formatted : " " + formatted
			#formatted
		end

		result = values_str.gsub!(/ +/, " ")
		result.gsub!(@numeric_re) {|num_str| format_value(num_str)} 
		result
	end
end

def parse_input
	options = {:files => nil, :key_words => nil, :precision => 12}
	parser = OptionParser.new do |opts|
		opts.banner = "ABINIT output diff tool\n"\
		 "Usage: ab_diff.rb [options]\n"\
		 "Usage examples:\n"\
     "ruby ab_diff.rb -f PdH.out -k xcart -p 6\n"\
		 'ruby ab_diff.rb -f PdH.out  -k "xcart, acell, acell"' + "\n"\
		 'ruby ab_diff.rb -f "Pd.out, PdH.out" -k "etotal, xcart"'
		opts.on('-f', '--files file_names ', Array,
		"if one file name given it will compare before and after computation variables",
		"if more file names given it will compare their after computation variables") do |files_names|
			texts = files_names.map { |f| {:name => f.strip, :text => File.read(f.strip)} }
			options[:files] = texts
		end
		opts.on("-k", "--keys key_words", Array,
						"ABINIT variables: acell, ecut, xcart, etc") do |key_words|
			options[:key_words] = key_words.map {|key_word| key_word.strip}
		end
		opts.on("-p", "--precision precision", Integer,
		"number of digits after decimal point",
		"default 12") do |precision|
			options[:precision] = precision
		end
		opts.on("-h", "--help", "help references") do
			puts opts
			exit
		end
	end
	parser.parse!

	raise "-f and -k are mandatory" unless options[:files] && options[:key_words]
	options
end

if __FILE__ == $0
	begin
	options = parse_input
	diff = ABINIT_Diff.new options[:key_words], options[:precision]
	diff.show(options[:files])
	rescue => e
		puts e.message
		puts "use -h key for help reference"
	end
end




