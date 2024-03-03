from glob import glob
from collections import defaultdict
import re, os
from depedit import DepEdit

deped = DepEdit()
deped.add_transformation("upos=/VERB/;func=/obj/;func=/iobj/\t#1>#2;#1>#3\t#1:morph+=Ditransitive=Yes")
deped.add_transformation("text=/^(?i)gon|wan/;text=/^(?i)na/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("text=/^(?i)dun/;text=/^(?i)no/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("text=/^(?i)out|got/;text=/^(?i)ta/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("text=/^(?i)c'?m/&misc=/.*SpaceAfter.No.*/;text=/^(?i)on/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("misc=/.*SpaceAfter.No.*/;text=/^(?i)[^A-Za-z]?(ll|d|m|ve|s)/&xpos=/VBP|MD|VHP|VBZ|VHZ|VB|VH/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("misc=/.*SpaceAfter.No.*/;xpos=/POS/\t#1.#2\t#1:misc+=SpaceAfter=No")
deped.add_transformation("misc=/.*SpaceAfter.No.*/&upos=/VERB|AUX/;lemma=/n[o']?t/\t#1.#2\t#1:misc+=SpaceAfter=No")

# def extract_date(tag):
#     # <date from:::"1939-09-01" to:::"1945-09-02">
#     matches = re.findall(r'(-?[0-9x][0-9x][0-9x][0-9x](?:-[0-9x][0-9x])?(?:-[0-9x][0-9x])?)',tag)
#     if len(matches) > 0:
#         return "--".join(matches)
#     else:
#         return ""

def make_html(conllu):
    global deped
    conllu = deped.run_depedit(conllu)
    
    html = ''
    speaker = ''  # Initialize speaker variable
    last_speaker = ''
    html_classes = set()  # Initialize HTML classes set
    head_sent_counter = 0
    caption_sent_counter = 0
    in_caption = False
    in_paragraph = False
    first_in_paragraph = False
    sentences = []
    
    # Process each line in the CoNLL-U data
    for line in conllu.split("\n"):
        if line.startswith("# "):  # Comment annotation
            if "newpar_block" in line and "head" in line:
                # Extract sentence counter using regex
                head_sent_counter = int(re.search(r'head [^|\n]*\(([0-9]+) s',line).group(1)) #head [^\n]*\(([0-9]+) s  #head [^|\n]*\(([0-9]+) s
                html+= f'<h1>' 
            # elif "newpar_block" in line and "ordered" in line:
            #     html += '<b><br>' 
            elif "speaker =" in line:             
                speaker = line.split("# speaker =")[1].strip()
                if last_speaker != speaker:
                    html += f'<br><b>{speaker}:</b></br> ' 
                    last_speaker = speaker
            elif "newpar_block" in line:
                if "caption" in line and "figure" in line:
                    caption_sent_counter = int(re.search(r'caption [^|\n]*\(([0-9]+) s',line).group(1))
                    #in_caption = True
                    html += f'<br></br><em><strong>' 
                    #html += '<b>'
                elif "ordered" in line:
                    html+= '<br>'
                    html += '</br> '
                elif "p" in line:
                    if caption_sent_counter >= 0: 
                        html += '</strong></em></br> ' 
                    in_paragraph = True
                    first_in_paragraph = True
                    if sentences:
                        # If sentences list is not empty, join sentences with a space 
                        html +=' '.join(sentences) + ' ' 
                        sentences = []  # Reset sentences list
                    #in_caption = False
        elif "\t" in line:  # Token processing
            parts = line.strip().split('\t')
            token = parts[1]
            if in_caption: 
                html += f'{token} '  # Wrap each token in </strong></em> tags
            elif in_paragraph:
                if first_in_paragraph:
                    html += '<p>'
                    first_in_paragraph = False
                html += f'{token} '   
            else:
                if "newpar_block" in line and "p" in line:
                    html += '<p>'
                # Check if it's a heading
                if head_sent_counter >= 0:
                    html += f'{token} '
                    #head_sent_counter -= 1  ## CHANGED!!!!
                else:
                    sentences.append(token)
                    # if speaker:
                    #     html += f'<p><strong>{speaker}:</strong>{token} </p>'
                    #     speaker = ''  # Reset speaker after usage
                    # else:
                    #     html += token + ' '
        elif line.strip() == '':  # Empty line indicates a new sentence
            if head_sent_counter >= 0:
                # If no more heading tokens left, close h1 tag
                html += '</h1>'
            elif caption_sent_counter >= 0: #elif in_caption: 
                html += f'</strong></em>'
                #in_caption = False
    if sentences:
        html += ' '.join(sentences)

    return html


if __name__ == "__main__":
    # Create a directory to store the HTML files if it doesn't exist
    html_dir = "./html"
    if not os.path.exists(html_dir):
        os.makedirs(html_dir)

    # Iterate over all files in the conllu folder
    conllu_folder = "./conllu"
    for filename in os.listdir(conllu_folder):
        # Check if the file is a CoNLL-U file
        if filename.endswith(".conllu"):
            # Read the contents of the CoNLL-U file
            with open(os.path.join(conllu_folder, filename), "r", encoding="utf-8") as conllu_file:
                conllu_content = conllu_file.read()
            
            # Generate HTML from the CoNLL-U content
            html_content = make_html(conllu_content)
            
            # Write the HTML content to a new file in the html folder
            html_filename = os.path.splitext(filename)[0] + ".html"
            with open(os.path.join(html_dir, html_filename), "w", encoding="utf-8") as html_file:
                html_file.write(html_content)