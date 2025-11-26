import sys
import os

TOKEN_MAP = {
    'begin': 1, 'end': 2, 'integer': 3, 'function': 4,
    'read': 5, 'write': 6, 'if': 7, 'then': 8, 'else': 9,
    ';': 10, '(': 11, ')': 12, ':=': 13, '*': 14, '-': 15,
    'ID': 16, 'CONST': 17,
    '<': 18, '<=': 19, '>': 20, '>=': 21, '=': 22, '<>': 23,
    'EOLN': 24, 'EOF': 25
}

CODE_TO_LEXEME = {v: k for k, v in TOKEN_MAP.items()}
CODE_TO_LEXEME[16] = 'ID'
CODE_TO_LEXEME[17] = 'CONST'

class Token:
    def __init__(self, text, type_code, line):
        self.text = text
        self.type_code = type_code
        self.line = line
    def __str__(self):
        return f"{self.text:<16} {self.type_code}"

class VarEntry:
    def __init__(self, vname, vproc, vkind, vtype, vlev, vadr):
        self.vname = vname
        self.vproc = vproc
        self.vkind = vkind
        self.vtype = vtype
        self.vlev = vlev
        self.vadr = vadr
    def __str__(self):
        return f"{self.vname:<16} {self.vproc:<16} {self.vkind} {self.vtype:<8} {self.vlev} {self.vadr}"

class ProEntry:
    def __init__(self, pname, ptype, plev, fadr, ladr):
        self.pname = pname
        self.ptype = ptype
        self.plev = plev
        self.fadr = fadr
        self.ladr = ladr
    def __str__(self):
        return f"{self.pname:<16} {self.ptype:<8} {self.plev} {self.fadr} {self.ladr}"

class Lexer:
    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.line = 1
        self.tokens = []
        self.errors = []
    def analyze(self):
        length = len(self.source)
        while self.pos < length:
            char = self.source[self.pos]
            if char == '\n':
                self.tokens.append(Token('EOLN', TOKEN_MAP['EOLN'], self.line))
                self.line += 1
                self.pos += 1
                continue
            if char.isspace():
                self.pos += 1
                continue
            if char.isalpha():
                start = self.pos
                while self.pos < length and (self.source[self.pos].isalnum()):
                    self.pos += 1
                word = self.source[start:self.pos]
                code = TOKEN_MAP.get(word, TOKEN_MAP['ID'])
                self.tokens.append(Token(word, code, self.line))
                continue
            if char.isdigit():
                start = self.pos
                while self.pos < length and self.source[self.pos].isdigit():
                    self.pos += 1
                num = self.source[start:self.pos]
                self.tokens.append(Token(num, TOKEN_MAP['CONST'], self.line))
                continue
            if char == ':':
                if self.pos + 1 < length and self.source[self.pos + 1] == '=':
                    self.tokens.append(Token(':=', TOKEN_MAP[':='], self.line))
                    self.pos += 2
                else:
                    self.errors.append(f"***LINE:{self.line} Unknown symbol ':'")
                    self.pos += 1
            elif char == '<':
                if self.pos + 1 < length and self.source[self.pos + 1] == '>':
                    self.tokens.append(Token('<>', TOKEN_MAP['<>'], self.line))
                    self.pos += 2
                elif self.pos + 1 < length and self.source[self.pos + 1] == '=':
                    self.tokens.append(Token('<=', TOKEN_MAP['<='], self.line))
                    self.pos += 2
                else:
                    self.tokens.append(Token('<', TOKEN_MAP['<'], self.line))
                    self.pos += 1
            elif char == '>':
                if self.pos + 1 < length and self.source[self.pos + 1] == '=':
                    self.tokens.append(Token('>=', TOKEN_MAP['>='], self.line))
                    self.pos += 2
                else:
                    self.tokens.append(Token('>', TOKEN_MAP['>'], self.line))
                    self.pos += 1
            elif char in ['=', '-', '*', '(', ')', ';']:
                self.tokens.append(Token(char, TOKEN_MAP[char], self.line))
                self.pos += 1
            else:
                self.errors.append(f"***LINE:{self.line} Unknown character '{char}'")
                self.pos += 1
        self.tokens.append(Token('EOF', TOKEN_MAP['EOF'], self.line))

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = tokens[0]
        self.errors = []
        self.var_table = []
        self.pro_table = []
        self.current_proc_name = 'main'
        self.current_level = 0
        self.var_adr_counter = 0
        self.pro_table.append(ProEntry('main', 'void', 0, 0, 0))
    def next_token(self):
        self.pos += 1
        while self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            if self.current_token.type_code != TOKEN_MAP['EOLN']:
                break
            self.pos += 1
    def match(self, expected_type_code, expected_lexeme=None):
        current_token = self.current_token
        if expected_type_code == TOKEN_MAP[';'] and current_token.type_code != TOKEN_MAP[';']:
            if current_token.type_code in [TOKEN_MAP['ID'], TOKEN_MAP['read'], TOKEN_MAP['write'], TOKEN_MAP['if'], TOKEN_MAP['end'], TOKEN_MAP['integer'], TOKEN_MAP['function']]:
                next_sym_name = current_token.text if current_token.type_code != TOKEN_MAP['ID'] else 'ID'
                self.error(f"Missing ';' before '{next_sym_name}'")
                return None
        if expected_type_code == TOKEN_MAP['end'] and current_token.text == 'edn': 
            self.error("Unknown keyword 'edn'")
            self.next_token()
            return current_token.text
        if current_token.type_code == expected_type_code and \
           (expected_lexeme is None or current_token.text == expected_lexeme):
            token_text = current_token.text
            self.next_token()
            return token_text
        else:
            expected_name = expected_lexeme if expected_lexeme else CODE_TO_LEXEME.get(expected_type_code, 'TOKEN')
            self.error(f"Expected '{expected_name}', but found '{current_token.text}'")
            self.next_token()
            return None
    def error(self, msg):
        self.errors.append(f"***LINE:{self.current_token.line} {msg}")
    def parse_program(self):
        self.parse_block()
        if self.pro_table:
            self.pro_table[0].ladr = self.var_adr_counter - 1
        if self.current_token.type_code != TOKEN_MAP['EOF']:
            self.error("Extra content after 'end'")
    def parse_block(self):
        self.current_level += 1
        if self.match(TOKEN_MAP['begin']): 
            self.parse_decl_list()
            self.match(TOKEN_MAP[';'])
            self.parse_exec_list()
            self.match(TOKEN_MAP['end'])
        if self.current_level > 0:
            self.current_level -= 1
    def parse_decl_list(self):
        while self.current_token.type_code in [TOKEN_MAP['integer']]:
            self.parse_declaration()
            if self.current_token.type_code == TOKEN_MAP[';']:
                next_idx = self.pos + 1
                while next_idx < len(self.tokens) and self.tokens[next_idx].type_code == TOKEN_MAP['EOLN']:
                    next_idx += 1
                if next_idx < len(self.tokens) and self.tokens[next_idx].type_code in [TOKEN_MAP['integer']]:
                    self.match(TOKEN_MAP[';'])
                else:
                    break
            else:
                break
    def parse_declaration(self):
        if self.current_token.type_code == TOKEN_MAP['integer']:
            self.match(TOKEN_MAP['integer'])
            if self.current_token.type_code == TOKEN_MAP['function']:
                self.parse_func_declaration()
            else:
                self.parse_var_declaration()
        else:
            pass
    def parse_var_declaration(self):
        var_name = self.match(TOKEN_MAP['ID'])
        if var_name:
            self.add_var(var_name, 0, 'integer')
    def parse_func_declaration(self):
        self.match(TOKEN_MAP['function'])
        func_name = self.match(TOKEN_MAP['ID'])
        old_proc = self.current_proc_name
        old_level = self.current_level
        old_adr = self.var_adr_counter
        self.var_adr_counter = 0
        self.match(TOKEN_MAP['('])
        if self.current_token.type_code == TOKEN_MAP['ID']:
            param_name = self.match(TOKEN_MAP['ID'])
            self.add_var(param_name, 1, 'integer')
        self.match(TOKEN_MAP[')'])
        self.match(TOKEN_MAP[';'])
        func_fadr = self.var_adr_counter
        self.current_proc_name = func_name
        self.current_level += 1
        self.parse_block()
        self.pro_table.append(ProEntry(
            func_name, 'integer', self.current_level, func_fadr, self.var_adr_counter - 1
        ))
        self.current_proc_name = old_proc
        self.current_level = old_level
        self.var_adr_counter = old_adr
    def parse_exec_list(self):
        self.parse_statement()
        while self.current_token.type_code == TOKEN_MAP[';']:
            self.match(TOKEN_MAP[';'])
            self.parse_statement()
    def parse_statement(self):
        tt = self.current_token.type_code
        if tt == TOKEN_MAP['read']: self.parse_read_statement()
        elif tt == TOKEN_MAP['write']: self.parse_write_statement()
        elif tt == TOKEN_MAP['if']: self.parse_condition_statement()
        elif tt == TOKEN_MAP['ID']: self.parse_assignment_statement()
        elif tt in [TOKEN_MAP['end'], TOKEN_MAP[';'], TOKEN_MAP['EOF']]:
            pass
        else:
            self.error("Expected a valid statement")
    def parse_condition_statement(self):
        self.match(TOKEN_MAP['if'])
        self.parse_cond_exp()
        self.match(TOKEN_MAP['then'])
        self.parse_statement()
        self.match(TOKEN_MAP['else'])
        if self.current_token.type_code in [TOKEN_MAP['end'], TOKEN_MAP[';'], TOKEN_MAP['EOF']]:
             self.error("Missing statement after 'else'")
        else:
             self.parse_statement()
    def parse_read_statement(self):
        self.match(TOKEN_MAP['read'])
        self.match(TOKEN_MAP['('])
        self.match(TOKEN_MAP['ID'])
        self.match(TOKEN_MAP[')'])
    def parse_write_statement(self):
        self.match(TOKEN_MAP['write'])
        self.match(TOKEN_MAP['('])
        self.match(TOKEN_MAP['ID'])
        self.match(TOKEN_MAP[')'])
    def parse_assignment_statement(self):
        self.match(TOKEN_MAP['ID'])
        self.match(TOKEN_MAP[':='])
        self.parse_expression()
    def parse_cond_exp(self):
        self.parse_expression()
        if self.current_token.type_code in range(TOKEN_MAP['<'], TOKEN_MAP['<>'] + 1):
            self.next_token()
        else:
            self.error("Expected relational operator")
        self.parse_expression()
    def parse_expression(self):
        self.parse_term()
        while self.current_token.type_code == TOKEN_MAP['-']:
            self.match(TOKEN_MAP['-'])
            self.parse_term()
    def parse_term(self):
        self.parse_factor()
        while self.current_token.type_code == TOKEN_MAP['*']:
            self.match(TOKEN_MAP['*'])
            self.parse_factor()
    def parse_factor(self):
        if self.current_token.type_code == TOKEN_MAP['CONST']:
            self.match(TOKEN_MAP['CONST'])
        elif self.current_token.type_code == TOKEN_MAP['ID']:
            self.match(TOKEN_MAP['ID'])
            if self.current_token.type_code == TOKEN_MAP['(']:
                self.match(TOKEN_MAP['('])
                self.parse_expression()
                self.match(TOKEN_MAP[')'])
        else:
            self.error("Expected an ID, constant, or expression (Factor)")
    def add_var(self, name, kind, vtype):
        entry = VarEntry(
            vname=name,
            vproc=self.current_proc_name,
            vkind=kind,
            vtype=vtype,
            vlev=self.current_level,
            vadr=self.var_adr_counter
        )
        self.var_table.append(entry)
        self.var_adr_counter += 1
    def parse(self):
        self.parse_program()
        return self.errors, self.var_table, self.pro_table

def main():
    if len(sys.argv) < 2:
        print("Usage: python <filename>.py <inputfile.min> [output_prefix]")
        return
    input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        base_name = sys.argv[2]
    else:
        base_name = os.path.splitext(input_file)[0]
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read() + '\n'
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
    lexer = Lexer(source_code)
    lexer.analyze()
    with open(f"{base_name}.dyd", 'w', encoding='utf-8') as f:
        for t in lexer.tokens:
            f.write(str(t) + '\n')
    all_errors = lexer.errors
    parser = Parser(lexer.tokens)
    parser_errors, var_table, pro_table = parser.parse()
    all_errors.extend(parser_errors)
    with open(f"{base_name}.err", 'w', encoding='utf-8') as f:
        if all_errors:
            f.write('\n'.join(all_errors) + '\n')
    with open(f"{base_name}.var", 'w', encoding='utf-8') as f:
        for v in var_table:
            f.write(str(v) + '\n')
    with open(f"{base_name}.pro", 'w', encoding='utf-8') as f:
        for p in pro_table:
            f.write(str(p) + '\n')
    print(f"Analysis complete. Results in {base_name}.* files. Total errors: {len(all_errors)}")

if __name__ == '__main__':
    main()