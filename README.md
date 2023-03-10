# Projeto
Projeto voltado para a programação das bombas hidráulicas para otimização energética em sistemas de abastecimento de água utilizando o solver CPLEX e o software EPANET.

# Proposta
Desenvolver um modelo computacional, integrado com o software EPANET, para programação de bombas hidráulicas para otimização energética em sistemas de abastecimento de água, a partir da linguagem de programação Python, junto com as bibliotecas Pyomo, Pandas, Numpy e Wntr.

# Contribuição
Desenvolvido por: Larissa de Castro Bonadio

Orientação: Edilaine Martins Soler

# Descrição do Projeto
O software desenvolvido recebe o arquivo de dados (extensão .INP), gerado no programa EPANET, junto com as informações do usuário para em seguida executar o modelo matemático desenvolvido por Parras (2021), que apresenta a programação da operação das bombas hidráulicas do sistema. Com a programação obtida, sua viabilidade é verificada, utilizando a biblioteca EpanetTools.

# Atenção
1. Para executar o arquivo de dados (extensão .INP), o arquivo não pode possuir palavras com acento ou 'ç';

2. Se um determinado nó é consumidor, o padrão que define sua demanda deve possuir o mesmo nome que o reservatório responsável por suprir a demanda.
    Exemplo: O reservatório 6 é responsável por suprir a demanda do nó consumidor 9, dessa forma, o padrão que define o valor da demanda deve ser nomeado '6';