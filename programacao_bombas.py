def informacao(M, rede, t, nome_arquivo):
    global m, T, wn, nome_arq
    wn = rede
    m  = M
    T  = t
    nome_arq = nome_arquivo
    
    if (escreve_programacao(definir_programacao(m))):
        return True
    else:
        return False
    
def definir_programacao(m):
    programacao_completa = ''
    
    for i, p, e in m.x:
        valor_atual = round(m.X[i, p, e, 0](), 2)
        status = bool(valor_atual)
        for t in range(1, T+1):
            if valor_atual != round(m.X[i, p, e, t](), 2):
                horario = faz_horario(t, round(m.X[i, p, e, t-1](), 2), round(m.X[i, p, e, t](), 2))
                programacao_completa += grava_horario(i, horario[0], status)
                status = not status
                if t < T:
                    valor_atual = round(m.X[i, p, e, horario[1]](), 2)
                
    for i, e, r in m.y:
        valor_atual = round(m.Y[i, e, r, 0](), 2)
        status = bool(valor_atual)
        for t in range(1, T+1):
            if valor_atual != round(m.Y[i, e, r, t](), 2):
                horario = faz_horario(t, round(m.Y[i, e, r, t-1](), 2), round(m.Y[i, e, r, t](), 2))
                programacao_completa += grava_horario(i, horario[0], status)
                status = not status
                if t < T:
                    valor_atual = round(m.Y[i, e, r, horario[1]](), 2)
                    
    for i, r, j in m.z:
        valor_atual = round(m.Z[i, r, j, 0](), 2)
        status = bool(valor_atual)
        for t in range(1, T+1):
            if valor_atual != round(m.Z[i, r, j, t](), 2):
                horario = faz_horario(t, round(m.Z[i, r, j, t-1](), 2), round(m.Z[i, r, j, t](), 2))
                programacao_completa += grava_horario(i, horario[0], status)
                status = not status
                if t < T:
                    valor_atual = round(m.Z[i, r, j, horario[1]](), 2)
          
    return programacao_completa              
    
def faz_horario(t, anterior, atual):
    horario = ''
    periodo = ''
    
    if t > 12:
        periodo = 'PM'
            
    else:
        periodo = 'AM'
    
    if atual > 0.0 and atual < 1.0:
        if anterior == 0.0:
            horario = transforma_hora(t) + ':' + '00' + ' ' + periodo  
        if anterior == 1.0:
           horario = transforma_hora(t) + ':' + transforma_minuto(atual) + ' ' + periodo 
           t = t + 1
    else:
        if anterior > 0.0 and anterior < 1.0:
            horario = transforma_hora(t-1) + ':' + transforma_minuto(anterior) + ' ' + periodo
        if anterior == 0.0 or anterior == 1.0:
            horario = transforma_hora(t) + ':' + '00' + ' ' + periodo  
    
    return horario, t 
    
def transforma_hora(horario):
    
    if horario == 0 or horario == 24:
        horario = '00'
        
    if horario == 1 or horario == 13:
        horario = '01'
            
    if horario == 2 or horario == 14:
        horario = '02'
            
    if horario == 3 or horario == 15:
        horario = '03'
        
    if horario == 4 or horario == 16:
        horario = '04'
        
    if horario == 5 or horario == 17:
        horario = '05'
        
    if horario == 6 or horario == 18:
        horario = '06'
            
    if horario == 7 or horario == 19:
        horario = '07'
            
    if horario == 8 or horario == 20:
        horario = '08'
        
    if horario == 9 or horario == 21:
        horario = '09'
        
    if horario == 10 or horario == 22:
        horario = '10'    

    if horario == 11 or horario == 23:
        horario = '11'        
        
    return str(horario)    
    
def transforma_minuto(tempo):
    minuto = str(int(round(tempo, 2) * 60))
    if int(minuto) < 10:
        minuto = '0' + str(minuto)
    return str(minuto)

def grava_horario(id_bomba, horario, status):
    controle = ''
    
    if id_bomba in wn.pump_name_list:
        controle = 'PUMP ' 
     
    else:
        controle = 'LINK '
        
    if status == True:
        status = str(' CLOSED')

    else:
        status = str(' OPEN  ')
        
    controle += str(id_bomba) + status + ' AT CLOCKTIME ' + horario + '\n'

    return controle


def escreve_programacao(controle):
    regras  = '\n[CONTROLS] \n' 
    regras += controle
    regras += '[END]\n'
     
    with open(nome_arq, 'r') as file:
        data = file.read()
        data = data.replace('\n[END]', regras)
        
    with open(nome_arq, 'w') as file:
        file.write(data)  
    return True

def apaga_programacao(nome_arquivo):
    with open(nome_arquivo, 'r') as arq_leitura:
        texto = arq_leitura.readlines()
        with open(nome_arquivo, 'w') as arq_escrita:
            for linha in texto:
                if 'AT CLOCKTIME' not in linha:
                    if '[CONTROLS]' not in linha:
                        arq_escrita.write(linha)