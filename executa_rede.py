from epanettools import epanet2 as et
import wntr

def acessa_arquivo(rede):
    global nome_arq, wn
    #   Acessando o modelo de rede
    nome_arq = rede
    wn = wntr.network.WaterNetworkModel(nome_arq + '.inp')
    simula_arq()
    
def simula_arq():
    
    result = False
    #while result == False:
    if result == False:
        arq_dados  = str(nome_arq) + '.inp' 
        arq_report = str(nome_arq) + '.rpt'
        arq_bin    = str(nome_arq) + '.bin'
    
        et.ENopen(arq_dados, arq_report, arq_bin)
        et.ENsolveH()
        et.ENreport()
        et.ENclose() 
        result = leitura_relatorio(arq_report)
    
def leitura_relatorio(arq_report):
    with open(arq_report, 'r') as arquivo:
        texto = arquivo.readlines()
    for frase in texto:
        if 'WARNING' in frase:
            verifica_alerta(frase)
    
    #return False
        
        #return True
    
def verifica_alerta(alerta):
    
    #   Identifica o elemento que está associado ao erro / advertencia
    if 'closed because cannot deliver head at' in alerta:
        id_obj = identifica_elemento(alerta)
        tipo_alerta(1, id_obj)
        
    if 'System disconnected because of' in alerta:
        id_obj = identifica_elemento(alerta)
        tipo_alerta(2, id_obj)
    
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
              

def tipo_alerta(tipo, id_obj):    
    #   Alerta 1: Pump / Link não consegue entregar demanda no horário
    if tipo == 1:
        bomba = wn.get_link(id_obj)
        if bomba in wn.pump_name_list:
            bomba.initial_status(bomba, 'Closed')    
    
    #   Alerta 2: Pressão negativa durante a simulação - aumentar em 10% o diamentro dos trechos associados aos nós que foram desconetados
    if tipo == 2:
        trecho = wn.get_link(id_obj)
        if trecho.start_node_name in wn.pump_name_list:
            bomba = trecho.start_node_name
        if trecho.end_node_name in wn.pump_name_list:
            bomba = trecho.end_node_name
        
        bomba = wn.get_link(bomba)
        
        if bomba.pump_curve_name in wn.curve_name_list:
            curva = wn.get_curve(bomba.pump_curve_name)
            vazao = round(3600 * float(curva.points[0][0]), 3) + (0.05 * (round(3600 * float(curva.points[0][0]), 3)))
            #print(vazao) # trocar no arquivo
            
#acessa_arquivo('rede_status')
