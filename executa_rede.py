from epanettools import epanet2 as et
import wntr

def acessa_arquivo(rede):
    global nome_arq, wn
    
    #   Acessando o modelo de rede
    nome_arq = rede
    wn = wntr.network.WaterNetworkModel(nome_arq)
    return simula_arq()
    
def simula_arq():
    global arq_report
    
    resultado = False
    if resultado == False:
        arq = nome_arq.split('.inp')[0]
        arq_dados  = str(arq) + '.inp' 
        arq_report = str(arq) + '.rpt'
        arq_bin    = str(arq) + '.bin'
    
        et.ENopen(arq_dados, arq_report, arq_bin)
        et.ENsolveH()
        et.ENreport()
        et.ENclose() 
        resultado = leitura_relatorio() 
    
    return resultado 
        
    
def leitura_relatorio():    
    #   Verifica se existe a alguma advertência, caso não exista, a simulação foi bem sucedida
    arq = open(arq_report, 'r')
    if 'WARNING' not in arq.read():
        return True
    
    # ----------------------------------------- #
    #   Se existe advertência / erro, vai verificar o alerta do relatório
    with open(arq_report, 'r') as arquivo:
        texto = arquivo.readlines()
    for frase in texto:
        if 'WARNING' in frase:
            verifica_alerta(frase)
            return False
    
def verifica_alerta(alerta):
    
    #   Bomba fechada porque não consegue entregar água
    if 'closed because cannot deliver head at' in alerta:
        alerta = alerta.split('at')[0]      # Retira o horário (para não confundir a identificação do objeto)
        id_obj = identifica_elemento(alerta)
        tipo_alerta(1, id_obj)
        
    #   Válvula está aberta mas não consegue entregar água
    if 'open but cannot deliver flow at' in alerta:
        alerta = alerta.split('at')[0]      # Retira o horário (para não confundir a identificação do objeto)
        id_obj = identifica_elemento(alerta)
        tipo_alerta(1, id_obj)
        
    #   Durante a simulação houve pressão negativa
    if 'Negative pressures at' in alerta:    
        id_nos = []
        with open(arq_report, 'r') as arquivo:
            texto = arquivo.readlines()
        for frase in texto:
            if 'disconnected at' in frase:
                alerta = frase.split(' at')[0]
                id_nos.append(identifica_elemento(alerta))
                id_nos[:] = list(set(id_nos))               #   Retira os id's repetidos
        tipo_alerta(2, id_nos)
    
def identifica_elemento(alerta):
    pega_id = []
    id_obj = ''
    
    #   Pega o id (que são números) da mensagem de alerta
    for caractere in alerta:
        if caractere.isdigit():
            pega_id.append(caractere)
            
    id_obj = id_obj.join(pega_id)

    #   Verifica se o elemento é uma bomba
    for i in wn.pump_name_list:
        if i == id_obj:
           return i
    
    #   Verifica se o elemento é um trecho
    for i in wn.pipe_name_list:
        if i == id_obj:
            return i
    
    #   Verifica se o elemento é uma válvula
    for i in wn.valve_name_list:
        if i == id_obj:
            return i

def tipo_alerta(tipo, id_obj): 
    status = ''
    id_trecho = []
    
    #   Alerta 1: Pump / Link não consegue entregar demanda no horário
    if tipo == 1:
        status += id_obj + '    Closed	;\n'
        escreve_alteracao(status, 1)
    
    #   Alerta 2: Pressão negativa durante a simulação - pega o ID do trecho para saber as informações sobre ele
    if tipo == 2:
        id_trecho = []
        for i in id_obj:
            for pipe, trecho in wn.pipes():
                if trecho.start_node_name == i or trecho.end_node_name == i:
                    id_trecho.append(trecho.name)        
    
    #   Retira os trechos repetidos
    id_trecho[:] = list(set(id_trecho))                
    
    #   Para cada trecho encontrado vai ser feita uma alteração
    for i in id_trecho:
        trecho = wn.get_link(i)
        escreve_alteracao(trecho, 2)
       
def escreve_alteracao(comando, tipo_alt): 
    
    #   Verifica se o STATUS já foi inserido no arquivo 
    status_existe = False
    if tipo_alt == 1:
        with open(nome_arq, 'r') as arq_leitura:
            texto = arq_leitura.readlines()
            for linha in texto:
                if comando in linha:
                    status_existe = True
        
    #   Erro 01: não consegue enviar água - então a bomba/válvula começa fechada
    if tipo_alt == 1 and status_existe == False:
        with open(nome_arq, 'r') as arq_leitura:
            texto = arq_leitura.readlines()
            with open(nome_arq, 'w') as arq_escrita:
                for linha in texto:
                    if 'Status/Setting' in linha:
                        arq_escrita.write(linha)
                        arq_escrita.write(comando)
                    else:
                        arq_escrita.write(linha) 
    
    #   Erro 02: pressão negativa - então aumenta o diâmetro da tubulação ligada as bombas que foram desligadas
    if tipo_alt == 2:
        lin_altera = altera_trecho(comando)
        
        with open(nome_arq, 'r') as arq_leitura:
            texto = arq_leitura.readlines()
            with open(nome_arq, 'w') as arq_escrita:
                for linha in texto:
                    if lin_altera[0:32] in linha:
                        arq_escrita.write(lin_altera)
                    else:
                        arq_escrita.write(linha) 
                        
def altera_trecho(trecho):
    linha_alt  = ' '
    esp1 = '              	'
    esp2 = '         	'
    
    #   A cada iteração o diâmetro aumenta em 15%
    novo_diametro = round(1000 * (trecho.diameter + (trecho.diameter * 0.15)), 0)
                                                                                                                
    linha_alt += str(trecho.name)          + esp1 + str(trecho.start_node_name)  + esp1 
    linha_alt += str(trecho.end_node_name) + esp1 + str(round(trecho.length, 0)) + esp2
    linha_alt += str(novo_diametro)        + esp2 + str(round(trecho.roughness,3)) + esp2
    linha_alt += str(round(trecho.minor_loss, 0))    + esp2 + str(trecho.status) + '  	;\n'
    
    return linha_alt