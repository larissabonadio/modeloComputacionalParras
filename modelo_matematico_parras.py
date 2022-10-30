# Italação das bibliotecas a partir do terminal do VSCode
# pip Install pyomo
# pip Install pandas
# pip Install numpy
# pip Install wntr
# pip Install mip

# Bibliotecas 
import pyomo.environ as pyo
from   pyomo.opt import SolverFactory
import numpy as np
#import pandas as pd
import wntr
import programacao_bombas
#import sys

################################################### Informações da Janela e do Arquivo INP ################################################### 
def info_adicional(tubulacao, demanda, taxa_dem, ultrapassagem, custo_acionamento, aMax, dMax, gMax, bMax, eta, trecho): 

    global tipo_tubulacao, D, td, u, ca
    global alfaMax, deltaMax, gamaMax, betaMax
    global lista_eta, trecho_transf
    
    lista_eta = []
    
    if tubulacao == 1:
        tipo_tubulacao = 'NOVA'
    else:
        tipo_tubulacao = 'VELHA'

    D  = float(demanda)    
    td = float(taxa_dem)
    u  = float(ultrapassagem) / 100
    ca = float(custo_acionamento)
    alfaMax  = int(aMax)
    deltaMax = int(dMax)
    gamaMax  = int(gMax)
    betaMax  = int(bMax)
    trecho_transf = trecho
    lista_eta.append(str(eta))
    
#    print(tipo_tubulacao, D, td, u, ca, alfaMax, deltaMax, gamaMax, betaMax, lista_eta)

def leitura_arquivo(nome_arq):
    
    global wn, rendimento_bomba, P, T, Nh, g, no_consumidor, reservatorios
    global nc, ne, nt, ns, id_superf, id_elevac, id_transf
    global nome_arquivo
    
    #   Acessando o modelo de rede
    wn = wntr.network.WaterNetworkModel(nome_arq)
    nome_arquivo = nome_arq
    #   Rendimento das bombas do sistema (todas as bombas do sistemas terão o mesmo rendimento)
    rendimento_bomba = float(wn.options.energy.global_efficiency / 100) 
    #rendimento_bomba = 0.7
    #   Lista com o nome dos pontos de captação (reservatório)
    P  = wn.reservoir_name_list                                         
    
    #   Duração total do período de simulação
    T  = int((wn.options.time.duration) / 3600)                         
    
    #   Número de horas em cada período (normalmente 1h)
    Nh = (wn.options.time.pattern_timestep) / 3600 

    #   Constante de gravidade            
    g  = 9.8              
    
    #   Lista dos nós que possuem demanda (demanda associada ao reservatório)
    no_consumidor = []                                                  
    
    #   Lista dos tanques que são considerados reservatórios (tira o tanque que é ETA)
    reservatorios = []                  

    #   Lista dos reservátorios - tirando o ETA
    for tank, tanque in wn.tanks():
        if tanque.name not in lista_eta:
            reservatorios.append(tanque.name)

    #   Lista com o ID do tipo de Bomba -- Também informa a quantidade de cada tipo de bomba
    nc = []
    ns = []
    ne = []
    nt = []
    
    #   Lista que vai guardar os índices de cada tipo de bomba
    id_elevac = []
    id_transf = []
    id_superf = [] 

    #   Se teve inclusão na janela acrescentando o id do trecho que fica entre os dois reservatórios            
    nt.append(trecho_transf) 

    #   Chama o modelo para obter a programação das bombas
    if(solucao_modelo()):
        return True
    else:
        return False        
        
##################################################### Funções auxiliares p/ a Rede ##################################################
#   Função que classifica as bombas e retorna a lista com o nome delas em cada tipo
def classifica_bomba():    
    for pump, bomba in wn.pumps():  
        
        # Se a bomba está ligada a algum reservatório, então a bomba é de captação superficial
        if (bomba.start_node_name in wn.reservoir_name_list) or (bomba.end_node_name in wn.reservoir_name_list):
            nc.append(bomba.name)
        
        # Se a bomba está ligada ao ETA, então a bomba é de elevação
        elif (bomba.start_node_name in lista_eta) or (bomba.end_node_name in lista_eta):
            ne.append(bomba.name)
        
        # Se a bomba está ligada a um tanque e esse tanque não está na lista do ETA, então é de transferência 
        elif (bomba.start_node_name in wn.tank_name_list) or (bomba.end_node_name in wn.tank_name_list):
            if bomba.start_node_name in lista_eta:    
                nt.append(bomba.name)
            elif bomba.end_node_name not in lista_eta:
                nt.append(bomba.name)
        
        # Caso contrário a bomba é de captação subterrânea
        else:
            ns.append(bomba.name)
         
#   Função que retorna a altura geométrica
def altura_geometrica (node1, node2):
    
    if node1 in wn.reservoir_name_list: 
        node1 = wn.get_node(node1)
        cota1 = node1.base_head              
    
    if node1 in wn.tank_name_list:
        node1 = wn.get_node(node1)
        cota1 = node1.elevation
            
    if node2 in wn.reservoir_name_list:
        node2 = wn.get_node(node2)
        cota2 = node2.base_head
    
    if node2 in wn.tank_name_list:
        node2 = wn.get_node(node2)
        cota2 = node2.elevation 
    
    if node2 in wn.node_name_list:
        for pipe, trecho in wn.pipes():
            if node2 == trecho.start_node_name:
                node2 = trecho.end_node_name
                if node2 in wn.tank_name_list:
                    node2 = wn.get_node(node2)
                    cota2 = node2.elevation 
    return abs(cota1 - cota2)

#   Função que define o valor do fator de atrito de Darcy–Weisbach
def fator_atrito_dw(tipo_bomba):
    
    if tipo_bomba == 'CAPTACAO':
        if tipo_tubulacao == 'NOVA':
            return 0.020
        else:
            return 0.054
    if tipo_bomba == 'ELEVACAO':
        if tipo_tubulacao == 'NOVA':
            return 0.019
        else:
            return 0.048
    if tipo_bomba == 'TRANSFERENCIA':
        if tipo_tubulacao == 'NOVA':
            return 0.025
        else:
            return 0.072
    if tipo_bomba == 'ABASTECIMENTO':
        if tipo_tubulacao == 'NOVA':
            return 0.019
        else:
            return 0.046  
        
#   Função que retorna o comprimento da tubulação especificada (em metros)
def comprimento_tubulacao(node):
    for pipe, trecho in wn.pipes():
        if trecho.start_node_name == node:
            return trecho.length
        
#   Função que retorna o diametro da tubulação especificada (em metros)
def diametro_tubulacao(node):
    for pipe, trecho in wn.pipes():
        if trecho.start_node_name == node:
            return trecho.diameter

#   Função que retorna o coeficiente de rugosidade da tubulação especificada
def rugosidade_tubulacao(node):
    for pipe, trecho in wn.pipes():
        if trecho.start_node_name == node:
            return trecho.roughness
        
#   Função que retorna a velocidade de escoamento
def velocidade(diametro, vazao):
    a = np.pi * pow(diametro, 2) / 4
    return (vazao / 3600) / a

#   Função que retorna a vazão da bomba
def vazao_bomba(id_bomba):
    bomba = wn.get_link(id_bomba)
    if bomba.pump_curve_name in wn.curve_name_list:
        curva = wn.get_curve(bomba.pump_curve_name)
    return round(3600 * float(curva.points[0][0]), 3)

#   PC - Potência consumida pela(s) bomba(s) de captação de ponto(s) de superficia(is)
def potencia_consumida(id_bomba):
    bomba = wn.get_link(id_bomba)
    
    #   Se a bomba for de captação de pontos superficiais
    if id_bomba in nc:        
        Hpe = altura_geometrica(bomba.start_node_name, lista_eta[0])
        Fpe = fator_atrito_dw('CAPTACAO')
        Lpe = comprimento_tubulacao(bomba.end_node_name)
        Dpe = diametro_tubulacao(bomba.end_node_name)
        Qpe = vazao_bomba(bomba.name)
        Vpe = round(velocidade(Dpe, Qpe), 3)
        return ((Hpe + Fpe * (Lpe/Dpe) * ((Vpe*Vpe)/(2*g))) * Qpe * 0.735499) / (270*rendimento_bomba)
    
    #   Se a bomba for de captação de pontos subterrânea
    
    #   Se a bomba for de elevação            
    if id_bomba in ne:
        Her = altura_geometrica(bomba.start_node_name, bomba.end_node_name)
        Fer = fator_atrito_dw('ELEVACAO')
        Ler = comprimento_tubulacao(bomba.end_node_name)
        Der = diametro_tubulacao(bomba.end_node_name)
        Qer = vazao_bomba(bomba.name)
        Ver = velocidade(Der, Qer)
        return ((Her + Fer * (Ler/Der) * ((Ver*Ver)/(2*g))) * Qer * 0.735499) / (270*rendimento_bomba)
        
    #   Se a bomba for de transferência
    if id_bomba in nt:
        Hrj = altura_geometrica(bomba.start_node_name, bomba.end_node_name)
        Frj = fator_atrito_dw('TRANSFERENCIA')
        Lrj = comprimento_tubulacao(bomba.end_node_name)
        Drj = diametro_tubulacao(bomba.end_node_name)
        Qrj = vazao_bomba(bomba.name)
        Vrj = velocidade(Drj, Qrj)
        #Hrj = 0
        return ((Hrj + Frj * (Lrj/Drj) * ((Vrj*Vrj)/(2*g))) * Qrj * 0.735499) / (270*rendimento_bomba)    

#   Função que retorna o valor da demanda que o reservatório deve atender
def demanda_reservatorio (id_reservatorio, t):
    return float(wn.get_pattern(str(id_reservatorio))[t-1])

#   Função que retorna o custo (em reais) do kW no período t
def custo_kW(t):
    return round(wn.get_pattern('PrecokWh')[t-1], 2)

#   Função que retorna o volume do reservatório
def base_reservatorio(id_reservatorio):
    if id_reservatorio in wn.tank_name_list:
        tanque = wn.get_node(id_reservatorio)
        return round(np.pi * pow(tanque.diameter / 2, 2), 2)

#   Função que retorna o reservatório que a bomba atende
def bomba_reservatorio(id_bomba):
    reserv = []
    bomba  = wn.get_link(id_bomba)
    for pipe, trecho in wn.pipes():
        if trecho.start_node_name == bomba.end_node_name:
            reserv.append(trecho.end_node_name)
    return reserv

#   Função que retorna o valor da vazão da bomba/trecho (valor por gravidade) que o reservatório utiliza
def vazao_reserv(i, r):
    if i in wn.pump_name_list:
        bomba = wn.get_link(i)
        if bomba.pump_curve_name in wn.curve_name_list:
            curva = wn.get_curve(bomba.pump_curve_name)
        return round(3600 * float(curva.points[0][0]), 3)
    if i in wn.pipe_name_list:
        return 25.0

def ligacao_reserv(id_obj):
    if id_obj in wn.pump_name_list or id_obj in wn.pipe_name_list:
        i = wn.get_link(id_obj)
        return i.start_node_name
    
#   Função que monta o vetor com os indices que cada variável de decisão vai usar
def set_indices():
    for i in nc:
        indice = []
        for p in P:
            for e in lista_eta:
                indice = (i, p, e)
                id_superf.append(indice)
    for i in ne:
        indice = []
        for e in lista_eta:
            for r in bomba_reservatorio(i):
                indice = (i, e, r)
                id_elevac.append(indice)
               
    for i in nt:
        indice = []
        for r in reservatorios:
            for q in reservatorios:
                if r != q and ligacao_reserv(i) == r:
                    indice = (i, r, q)
                    id_transf.append(indice)
                    
#   Função que retorna o status inicial da bomba (ligada ou desligada)
def status_bomba(i):
    if i in wn.pump_name_list or i in wn.pipe_name_list:
        id_bomba = wn.get_link(i)
        if str(id_bomba.initial_status) == 'Open':
            return 1
        else:
            return 0
        
#########################################################  MODELO #########################################################
def modelo_matematico():
    
    #   Inicializando componentes
    classifica_bomba()  
    set_indices()

    #   Inicializando modelo 
    modelo = pyo.ConcreteModel()
    m = modelo

    #   Parâmetros
    m.x  = pyo.Set(initialize=(id_superf))
    m.y  = pyo.Set(initialize=(id_elevac))
    m.z  = pyo.Set(initialize=(id_transf))
    m.T  = pyo.RangeSet(0, int(T))
    m.nc = pyo.Set(initialize=(nc))
    m.ns = pyo.Set(initialize=(ns))
    m.ne = pyo.Set(initialize=(ne))
    m.nt = pyo.Set(initialize=(nt))
    m.rs = pyo.Set(initialize=(reservatorios))
    m.eta= pyo.Set(initialize=(lista_eta))
    m.p  = pyo.Set(initialize=(P))
    
    #   Variáveis de Decisão
    # m.I   = pyo.Var(m.ns, m.T, within = pyo.PositiveReals, bounds=(0,1))
    m.X   = pyo.Var(m.x,  m.T, within = pyo.PositiveReals, bounds=(0,1))
    m.Y   = pyo.Var(m.y,  m.T, within = pyo.PositiveReals, bounds=(0,1))
    m.Z   = pyo.Var(m.z,  m.T, within = pyo.PositiveReals, bounds=(0,1))
    m.Phi = pyo.Var(m.rs, m.T, within = pyo.PositiveReals)
    
    # m.Delta = pyo.Var(m.i, m.T,  within = pyo.Binary, initialize=(0))
    m.Alfa  = pyo.Var(m.x, m.T, domain = pyo.Binary)
    m.Gama  = pyo.Var(m.y, m.T, domain = pyo.Binary)
    m.Beta  = pyo.Var(m.z, m.T, domain = pyo.Binary) 
    
    # m.Sns   = pyo.Var(m.i, m.T, within = pyo.Binary, initialize=(0))
    m.Anc   = pyo.Var(m.x, m.T, domain = pyo.Binary)
    m.Bne   = pyo.Var(m.y, m.T, domain = pyo.Binary)
    m.Cnt   = pyo.Var(m.z, m.T, domain = pyo.Binary)
    
    #   Simplificando a nomenclatura do modelo 
    #I   = m.I
    #Delta = m.Delta
    #Sns   = m.Sns
    X   = m.X
    Y   = m.Y
    Z   = m.Z
    Alfa = m.Alfa 
    Gama = m.Gama
    Beta = m.Beta
    Phi  = m.Phi
    Anc  = m.Anc
    Bne  = m.Bne
    Cnt  = m.Cnt
#################################################  FUNÇÃO OBJ E RESTRIÇÕES  #################################################

    def funcao_objetivo(m):
       obj  = sum((potencia_consumida(i) * X[i, p, e, t] * Nh * custo_kW(t)) + (Alfa [i, p, e, t] * ca) for i, p, e in m.x for t in range(1,T+1))
   #   obj += sum((potencia_consumida(i) * I[i, b, e, t] * Nh * custo_kW(t)) + (Delta[i, b, e, t] * ca) for i, b, e in m.ns for t in range(1,T+1))
       obj += sum((potencia_consumida(i) * Y[i, e, r, t] * Nh * custo_kW(t)) + (Gama [i, e, r, t] * ca) for i, e, r in m.y for t in range(1,T+1))
       obj += sum((potencia_consumida(i) * Z[i, r, j, t] * Nh * custo_kW(t)) + (Beta [i, r, j, t] * ca) for i, r, j in m.z for t in range(1,T+1) if i in wn.pump_name_list)
       obj += (D * td)
       return obj

    #   Cálculo da demanda contratada
    def restricao_01(m):
        R1  = sum(potencia_consumida(i) * X[i, p, e, t] * Nh for i, p, e in m.x for t in range(1,T+1))
    #   R1 += sum(potencia_consumida(i) * I[i, b, e, t] * Nh for i, b, e in m.ns for t in range(1,T+1))
        R1 += sum(potencia_consumida(i) * Y[i, e, r, t] * Nh for i, e, r in m.y for t in range(1,T+1))
        R1 += sum(potencia_consumida(i) * Z[i, r, j, t] * Nh for i, r, j in m.z for t in range(1,T+1) if i in wn.pump_name_list)
        return R1 <= (1.1 * D)
    
    #   Cálculo do volume de água nos reservatórios
    def restricao_02(m, r, t):
        if t == 0:
            return pyo.Constraint.Skip
        R = r
        R2  = (1 - 0) * Phi[r, t-1]
        R2 += sum(vazao_bomba(i)     * Y[i, e, r, t] * Nh for i, e, r in m.y if r == R)  
        #R2 += sum(vazao_bomba(i)    * I[i, b, e, t] * Nh for i, e, r in m.i if r == R)
        R2 += sum(vazao_reserv(i, r) * Z[i, r, j, t] * Nh for i, r, j in m.z if r != R)
        R2 -= sum(vazao_reserv(i, r) * Z[i, r, j, t] * Nh for i, r, j in m.z if r == R)
        R2 -= demanda_reservatorio(r, t)       
        return Phi[r, t] == R2
    
    #   Restrições para volume de água no reservatório
    def restricao_03(m, i, t):
        tanque = wn.get_node(i)
        if t == 0:
            return pyo.Constraint.Skip
        PhiMin = round(np.pi * pow(tanque.diameter / 2, 2) * tanque.min_level, 1)
        PhiMax = round(np.pi * pow(tanque.diameter / 2, 2) * tanque.max_level, 1)
        return (PhiMin, Phi[i, t], PhiMax)
    
    def restricao_04(m, i, t):
        if t == T:
            tanque = wn.get_node(i)
            lb = round(0.9 * round((np.pi * pow((tanque.diameter / 2), 2) * tanque.min_level), 2), 2)
            ub = round(1.1 * round((np.pi * pow((tanque.diameter / 2), 2) * tanque.min_level), 2), 2)
            return (lb, Phi[i, t], ub)
        else:
            return pyo.Constraint.Skip
    
    def restricao_05(m, i, t):
        tanque = wn.get_node(i)
        if t == 0:
            return Phi[i, 0] == round(np.pi * pow(tanque.diameter / 2, 2) * tanque.min_level, 1)
        return pyo.Constraint.Skip
    
    #   Restrição para vazão de água captada
    def restricao_06(m):
        R1 = sum(vazao_bomba(i) * X[i, p, e, t] * Nh for i, p, e in m.x for t in range(1,T+1))
        R2 = sum(vazao_bomba(i) * Y[i, e, r, t] * Nh for i, e, r in m.y for t in range(1,T+1))
        return R1 == R2
    
    #   Restrições de acionamentos das bombas
    def restricao_07(m, i, p, e):
        return sum(Alfa[i, p, e, t] for t in range(1,T+1))  <= alfaMax

    '''def restricao_08(m):
        return sum(Delta[i, t] for i in modelo.ns for t in range(1,T+1)) <= deltaMax'''
    
    def restricao_09(m, i, e, r):
        return sum(Gama[i, e, r, t] for t in range(1,T+1))  <= gamaMax
    
    def restricao_10(m, i, r, j):
        return sum(Beta[i, r, j, t] for t in range(1,T+1))  <= betaMax
    
    def restricao_11(m, i, p, e, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Anc[i, p, e, t] >= X[i, p, e, t]
    
    '''def restricao_12(m, i, d, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Sns[i, d, t] >= I[i, d, t]'''
    
    def restricao_13(m, i, e, r, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Bne[i, e, r, t] >= Y[i, e, r, t] 
    
    def restricao_14(m, i, r, j, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Cnt[i, r, j, t] >= Z[i, r, j, t]  
    
    def restricao_15(m, i, p, e, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Alfa[i, p, e, t] >= (Anc[i, p, e, t] - X[i, p, e, t-1])
    
    '''def restricao_16(m, i, d, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Delta[i, d, t] >= Sns[i, d, t] - I[i, d, t-1]'''
    
    def restricao_17(m, i, e, r, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Gama[i, e, r, t] >= (Bne[i, e, r, t] - Y[i, e, r, t-1])
    
    def restricao_18(m, i, r, j, t):
        if t == 0:
            return pyo.Constraint.Skip
        return Beta[i, r, j, t] >= (Cnt[ i, r, j, t] - Z[ i, r, j, t-1])   
    
    def restricao_19(m, i, p, e, t):
        if t == 0:
            return X[i, p, e, 0] == status_bomba(i)
        return pyo.Constraint.Skip

    '''def restricao_20(m, i, d, t):
        if t == 0:    
            return I[i, d, t] == status_bomba(i)
        return pyo.Constraint.Skip'''
    
    def restricao_21(m, i, e, r, t):
        if t == 0:
            return Y[i, e, r, t] == status_bomba(i)
        return pyo.Constraint.Skip
    
    def restricao_22(m, i, r, j, t):
        if t == 0:
            return Z[i, r, j, t] == status_bomba(i)
        return pyo.Constraint.Skip
       
    m.R01 = pyo.Constraint(rule = restricao_01)
    m.R02 = pyo.Constraint(m.rs, m.T, rule = restricao_02)
    m.R03 = pyo.Constraint(m.rs, m.T, rule = restricao_03)
    m.R04 = pyo.Constraint(m.rs, m.T, rule = restricao_04)
    m.R05 = pyo.Constraint(m.rs, m.T, rule = restricao_05)
    m.R06 = pyo.Constraint(rule = restricao_06)
    m.R07 = pyo.Constraint(m.x, rule = restricao_07)
  # m.R08 = pyo.Constraint(m.i, rule = restricao_08)
    m.R09 = pyo.Constraint(m.y, rule = restricao_09)
    m.R10 = pyo.Constraint(m.z, rule = restricao_10)
    m.R11 = pyo.Constraint(m.x, m.T, rule = restricao_11)
  # m.R12 = pyo.Constraint(m.i, m.T, rule = restricao_12)
    m.R13 = pyo.Constraint(m.y, m.T, rule = restricao_13)
    m.R14 = pyo.Constraint(m.z, m.T, rule = restricao_14)
    m.R15 = pyo.Constraint(m.x, m.T, rule = restricao_15)
  # m.R16 = pyo.Constraint(m.i, m.T, rule = restricao_16)
    m.R17 = pyo.Constraint(m.y, m.T, rule = restricao_17)
    m.R18 = pyo.Constraint(m.z, m.T, rule = restricao_18)
    m.R19 = pyo.Constraint(m.x, m.T, rule = restricao_19)
  # m.R20 = pyo.Constraint(m.i, m.T, rule = restricao_20)
    m.R21 = pyo.Constraint(m.y, m.T, rule = restricao_21)
    m.R22 = pyo.Constraint(m.z, m.T, rule = restricao_22)
    
    m.obj = pyo.Objective(rule = funcao_objetivo, sense = pyo.minimize)

    return m

############################################## Solução do Modelo ##############################################
def solucao_modelo():

    m = modelo_matematico()    
    #opt = SolverFactory("cbc", executable='C:\\Users\\laris\\Cbc\\cbc.exe')
    opt = SolverFactory("cplex")
    #opt = SolverFactory("gurobi")
    results = opt.solve(m)
#   results.write()
    #results = opt.solve(m, tee=True)
    ''' Testes para ver resultado do modelo 
    m.Phi.pprint()
    m.display()
    m.Phi.display()
    m.X.pprint()
    m.Y.pprint()
    m.Z.pprint()
    m.Phi.pprint() 
    m.Gama.pprint()
    m.Beta.pprint()
    m.Anc.pprint()
    m.Bne.pprint()
    m.Cnt.pprint()
    ''' 
    # print(programacao_bombas.informacao(m, wn, T, nome_arquivo))
    
    if(programacao_bombas.informacao(m, wn, T, nome_arquivo)):
        return True
    else:
        return False
    
#  TESTES LOCAIS NO FONTE
#       tubulação, demanda, td, ultrapassagem, ca, Amax, Dmax, Gmax, Bmax, link

#info_adicional(0, '18989.00', '5.12', '0', '2.0', '2', '5', '5', '5', '3', '16')
#leitura_arquivo('rede_status_ant.inp')
