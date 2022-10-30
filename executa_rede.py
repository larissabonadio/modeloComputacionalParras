from epanettools import epanet2 as et
import wntr

def acessa_arquivo(rede):
    global wn
    #   Acessando o modelo de rede
    wn = wntr.network.WaterNetworkModel(rede)
    
def simula_arq(rede):
    acessa_arquivo(rede)
    result = False
    while result == False:
        arq_dados  = str(rede) + '.inp' 
        arq_report = str(rede) + '.rpt'
        arq_bin    = str(rede) + '.bin'
    
        et.ENopen(arq_dados, arq_report, arq_bin)
        et.ENsolveH()
        et.ENreport()
        et.ENclose() 
        result = leitura_relatorio(arq_report)
    
def leitura_relatorio(arq_report):
    with open(arq_report, 'r', encoding=('utf-8')) as arquivo:
        texto = arquivo.readlines()
    for frase in texto:
        if 'WARNING' in frase:
            verifica_alerta(frase)
            return False
        return True
    
def verifica_alerta(alerta):
    if 'closed because cannot deliver head at' in alerta:
        print('fecha bomba 9')
        # -> status_inicial da bomba X = 0
   # if ''

def alerta_01(id_bomba):
    bomba = wn.get_link(id_bomba)
    if bomba.pump_curve_name in wn.curve_name_list:
        curva = wn.get_curve(bomba.pump_curve_name)
        print (round(3600 * float(curva.points[0][0]), 3))
    
#simula_arq('rede')

# clean up the created files
#et.file.remove("Net1.rpt")
#et.file.remove("Net1.bin")