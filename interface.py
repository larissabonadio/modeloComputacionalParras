import PySimpleGUI as sg
from os import path
import os.path
import pathlib 
import shutil
import wntr
import modelo_matematico_parras as modeloParras
import executa_rede as simulacao

#   Layout
sg.theme('Dark2')

layout_busca = [
    [sg.Text(''),
     sg.Input(key='caminho', size=(70, 60)), 
     sg.FileBrowse(' Procurar ', file_types=(("Arquivo INP", "*.inp"), ("ALL Files", "*.*"))), 
     sg.Submit(button_text=' Ok ', key=('ok'))
    ]
]

layout_info = [
    [sg.Text('Tipo de Tubulação:'),
     sg.Radio('Antiga', 'cano', key=('tubulacao'), pad=(3)),
     sg.Radio('Nova', 'cano', key=('tubulacao'), pad=(3)),
    ],
    [sg.Text('Demanda energética contratada por dia (kW)', pad=(3)),
     sg.Input(size=(7,15), key=('D'), pad=(3)),
    ],
    [sg.Text('Taxa para contratação de demanda energética (R$/kW)', pad=(3)),
     sg.Input(size=(7,15), key=('td'), pad=(3)),
    ],
    [sg.Text('Porcentagem  de ultrapassagem (%)', pad=(3)),
     sg.Input(size=(7,15), key=('u'), pad=(3)),
    ],
]
layout_bomba = [
    [sg.Text('Custo de acionamento das bombas (R$)', pad=(3)), sg.Input(size=(7,15), key=('ca'), pad=(3))     
    ], 
    [sg.Text('Número de acionamentos máximos para cada bomba de captação superficial', pad=(3)),
     sg.Input(size=(7,15), key=('alfaMax'), pad=(3)),
    ],
    [sg.Text('Número de acionamentos máximos para cada bomba de captação subterrânea', pad=(3)),
     sg.Input(size=(7,15), key=('deltaMax'), pad=(3)),
    ],
    [sg.Text('Número de acionamentos máximos para cada bomba de elevação', pad=(3)),
     sg.Input(size=(7,15), key=('gamaMax'), pad=(3)),
    ],
    [sg.Text('Número de acionamentos máximos para cada bomba de transferência', pad=(3)),
     sg.Input(size=(7,15), key=('betaMax'), pad=(3)),
    ],
]

layout_rede = [
    [sg.Text('Indique o ID do reservatório que representa a Estação de Tratamento de Água (ETA) da rede', pad=(3)),
     sg.Input(size=(7,15), key=('eta'), pad=(3))
    ],
    [sg.Text('Indique o ID do trecho que é usado para transferência entre reservatórios (Caso não exista insira "0")', pad=(3)),
     sg.Input(size=(7,15), key=('trecho'), pad=(3))
    ],
    [sg.Text('Indique o nome do padrão que define o costo do kW em cada periodo ', pad=(3)),
     sg.Input(size=(7,15), key=('custokW'), pad=(3))
    ],
    [sg.Text('Indique o número máximo de iteração ', pad=(3)),
     sg.Input(size=(7,15), key=('itMax'), pad=(3))
    ],
]

layout_baixar_arq = [
    [sg.Text('Click no botão Download para baixar o arquivo INP modificado', pad=(3))],
    [sg.Button(' Download ', key=('download'), pad=(3))],
]

layout = [
    [sg.Frame('Selecione o Arquivo INP'         , layout_busca      , visible = True  , key=('busca')   , size=(650, 60))],
    [sg.Frame('Informações Adicionais'          , layout_info       , visible = False , key=('info')    , size=(650, 130))],
    [sg.Frame('Informações sobre a(s) Bomba(s)' , layout_bomba      , visible = False , key=('bomba')   , size=(650, 160))],
    [sg.Frame('Informações dos Componentes'     , layout_rede       , visible = False , key=('rede')    , size=(650, 130))],
    [sg.Frame('Solução Viável Encontrada'       , layout_baixar_arq , visible = False , key=('solucao') , size=(400, 90))],
    [sg.Button(' Sair '                         , key=('sair')      , visible = False),
     sg.Button(' Executar '                     , key=('executar')  , visible = False),]
]  

janela = sg.Window('Execução de Arquivo', layout, resizable=True)    

#   Leitura do evento
def carrega_janela():
    while True:
        evento, valor = janela.read()
        if evento == sg.WIN_CLOSED or evento == 'sair':
            break
        else:
            processa_evento(evento, valor)
    janela.close()
        
def processa_evento(evento, valor):
    global novo_arq, wn
    nome_arq = valor['caminho']           
    if os.path.isfile(nome_arq):
        print('')
    else:
        sg.Popup('Verifique se o caminho e o nome do arquivo estão corretos.', title='Arquivo não foi encontrado')
        return
        
    if evento == 'ok':
        #   Copiar o arquivo para um novo e passar o novo para tratar as modificações
        novo_arq = os.path.dirname(nome_arq) + '\\' + pathlib.Path(nome_arq).stem + '_modificado.inp'  
        shutil.copy2(nome_arq, novo_arq)  
        wn = wntr.network.WaterNetworkModel(novo_arq)
        
        if(wn):
            atualiza_janela(2)
            return 
        else:
            sg.Popup('Não foi possível ler o Arquivo Selecionado, verifique-o e tente novamente', title='AVISO')
            return
        
    if evento == 'executar':
        if(verifica_campos(valor['tubulacao'], valor['D'], valor['td'], valor['u'], valor['ca'], valor['alfaMax'], valor['deltaMax'], valor['gamaMax'], valor['betaMax'], wn, valor['eta'], valor['trecho'], valor['itMax'], valor['custokW'])):
            if valor['eta'] in wn.tank_name_list and (valor['trecho'] in wn.pipe_name_list or valor['trecho'] == 0):
                modeloParras.info_adicional(valor['tubulacao'], valor['D'], valor['td'], valor['u'], valor['ca'], valor['alfaMax'], valor['deltaMax'], 
                                            valor['gamaMax'], valor['betaMax'], valor['eta'], valor['trecho'], valor['itMax'], valor['custokW'])        
                executa_modelo()
            else:
                sg.Popup('Verique se os valores foram inseridos de forma correta!')
                return
            
    if evento == 'download':        
        if os.path.exists(novo_arq):
            pathlib.Path(novo_arq).touch()
            sg.Popup("Arquivo foi salvo com sucesso!")
            janela.close()
            
        else:
            sg.Popup("Diretório não existe! Verifique o diretório do arquivo informado")
    
def executa_modelo():
    #   Faz a leitura do arquivo e das informações da rede e obtem a programação das bombas
    if(modeloParras.leitura_arquivo(novo_arq)):
        atualiza_janela(3)

    else:
        sg.Popup("Não foi possível encontrar uma solução viável para a rede informada")
        janela.close()
    
def atualiza_janela(jan):
    if jan == 1:
        janela['info'].update(visible = False)
        janela['busca'].update(visible = True)
        janela['executar'].update(visible = False)
        janela['sair'].update(visible = False)
             
    if jan == 2:
        janela['info'].update(visible = True) 
        janela['bomba'].update(visible = True)
        janela['rede'].update(visible = True)
        janela['executar'].update(visible = True)
        janela['sair'].update(visible = True)   
        
    if jan == 3:
        janela['busca'].hide_row()
        janela['info'].hide_row()
        janela['bomba'].hide_row()
        janela['rede'].hide_row()
        janela['executar'].hide_row()
        janela['sair'].hide_row()
        janela['solucao'].update(visible = True)
        
def isnumber(value):
    try:
         float(value)
    except ValueError:
         return False
     
    return True

def isinteger(value):
    try:
         int(value)
    except ValueError:
         return False
     
    return True
  
def verifica_campos(tubulacao, d, td, u, ca, aMax, dMax, gMax, bMax, rede, eta, trecho, iteracao, padraoCusto):
    
    if ((tubulacao == '') or (d == '') or (td == '') or (u == '') or (ca == '') or (aMax == '') or (dMax == '') or (gMax == '') or (bMax == '') or (rede == '') or (eta == '') or (trecho == '') or (iteracao == '')):
        sg.Popup('Todos os campos devem ser preenchidos!', title='AVISO')
        return False
    
    if (isnumber(d) == False):
        sg.Popup('O campo Demanda Energética deve ser um valor numérico.', title='AVISO')
        return False    
    
    if (isnumber(td) == False):
        sg.Popup('O campo Taxa para Contratação de Demanda Energética deve ser um valor numérico.', title='AVISO')
        return False
    
    if (isnumber(u) == False):
        sg.Popup('O campo Taxa de Ultrapassagem deve ser um valor numérico.', title='AVISO')
        return False
        
    if (isnumber(ca) == False):
        sg.Popup('O campo Custo de Acionamento deve ser um valor numérico.', title='AVISO')
        return False
            
    if(isinteger(aMax) == False):
        sg.Popup('O campo Número de Acionamento da(s) bomba(s) de captação superficial deve ser um valor inteiro.', title='AVISO')
        return False
        
    if (isinteger(dMax) == False): 
        sg.Popup('O campo Número de Acionamento da(s) bomba(s) de captação subterrânea deve ser um valor inteiro.', title='AVISO')
        return False
        
    if (isinteger(gMax) == False): 
        sg.Popup('O campo Número de Acionamento da(s) bomba(s) de elevação deve ser um valor inteiro.', title='AVISO')
        return False
        
    if (isinteger(bMax) == False):
        sg.Popup('O campo Número de Acionamento da(s) bomba(s) de transferência deve ser um valor inteiro.', title='AVISO')
        return False
    
    if str(eta) not in rede.tank_name_list:
        sg.Popup('O ID que representa o ETA não encontra-se na lista de tanques, verifique o arquivo e tente novamente.', title='AVISO')
        return False
                
    if str(trecho) not in rede.pipe_name_list:
        if str(trecho) != '0':
            sg.Popup('O ID que representa o TRECHO que faz a transferência entre reservatórios não encontra-se na lista de trechos, verifique o arquivo e tente novamente\n Caso não exista digite "0"')
            return False
    
    if (isinteger(iteracao) == False or str(iteracao) <= '0'):
        sg.Popup('Número de iterações máxima deve ser maior que 0')

    if (str(padraoCusto) not in rede.pattern_name_list):
        sg.Popup('Nome do padrão inserido não encontra-se na lista de padrões, verifique o arquivo novamente.')
    
    return True    