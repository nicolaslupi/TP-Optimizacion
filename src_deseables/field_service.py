# Con Restricciones Deseables

import sys
import cplex
import numpy as np

TOLERANCE =10e-6

class Orden:
    def __init__(self):
        self.id = 0
        self.beneficio = 0
        self.trabajadores_necesarios = 0

    def load(self, row):
        self.id = int(row[0])
        self.beneficio = int(row[1])
        self.trabajadores_necesarios = int(row[2])


class FieldWorkAssignment:
    def __init__(self):
        self.cantidad_trabajadores = 0
        self.cantidad_ordenes = 0
        self.ordenes = []
        self.conflictos_trabajadores = []
        self.ordenes_correlativas = []
        self.ordenes_conflictivas = []
        self.ordenes_repetitivas = []


    def load(self,filename):
        # Abrimos el archivo.
        f = open(filename)

        # Leemos la cantidad de trabajadores
        self.cantidad_trabajadores = int(f.readline())

        # Leemos la cantidad de ordenes
        self.cantidad_ordenes = int(f.readline())

        # Leemos cada una de las ordenes.
        self.ordenes = []
        for _ in range(self.cantidad_ordenes):
            row = f.readline().split(' ')
            orden = Orden()
            orden.load(row)
            self.ordenes.append(orden)

        # Leemos la cantidad de conflictos entre los trabajadores
        cantidad_conflictos_trabajadores     = int(f.readline())

        # Leemos los conflictos entre los trabajadores
        self.conflictos_trabajadores = []
        for _ in range(cantidad_conflictos_trabajadores):
            row = f.readline().split(' ')
            self.conflictos_trabajadores.append(list(map(int,row)))

        # Leemos la cantidad de ordenes correlativas
        cantidad_ordenes_correlativas = int(f.readline())

        # Leemos las ordenes correlativas
        self.ordenes_correlativas = []
        for _ in range(cantidad_ordenes_correlativas):
            row = f.readline().split(' ')
            self.ordenes_correlativas.append(list(map(int,row)))

        # Leemos la cantidad de ordenes conflictivas
        cantidad_ordenes_conflictivas = int(f.readline())

        # Leemos las ordenes conflictivas
        self.ordenes_conflictivas = []
        for _ in range(cantidad_ordenes_conflictivas):
            row = f.readline().split(' ')
            self.ordenes_conflictivas.append(list(map(int,row)))


        # Leemos la cantidad de ordenes repetitivas
        cantidad_ordenes_repetitivas = int(f.readline())

        # Leemos las ordenes repetitivas
        self.ordenes_repetitivas = []
        for _ in range(cantidad_ordenes_repetitivas):
            row = f.readline().split(' ')
            self.ordenes_repetitivas.append(list(map(int,row)))

        f.close()


def get_instance_data():
    file_location = sys.argv[1].strip()
    instance = FieldWorkAssignment()
    instance.load(file_location)
    return instance


def add_constraint_matrix(my_problem, data):
    """ Función que carga restricciones al problema """

    """ R1 """
    # Un trabajador en un turno de un día, solo puede estar como mucho en una orden
    for i in range(5):
        for d in range(6):
            for t in range(data.cantidad_trabajadores):
                indices = list(map(int, data.indices_Xidto[i,d,t,:].flatten()))
                values = [1] * data.cantidad_ordenes
                row = [indices,values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])

    """ R2 """
    # Si no están los trabajadores necesarios para una orden, la D se apaga (la orden no se cobra)
    for o in range(data.cantidad_ordenes):
        indices = list(map(int, data.indices_Xidto[:,:,:,o].flatten())) + [int(data.indices_D[o])]
        values = [1] * 5*6*data.cantidad_trabajadores + [-data.ordenes[o].trabajadores_necesarios]
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])


    ###################################################
    """ Trabajadores de una orden en el mismo turno """
    ###################################################

    """ R3 """
    # Una orden no se puede hacer en más de un turno
    for o in range(data.cantidad_ordenes):
        indices = list(map(int, data.indices_Kido[:,:,o].flatten()))
        values = [1] * 5*6
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])

    """ R4 """
    # La orden o se prende en el turno i día d, si hay algún trabajador asignado a esa orden en ese turno
    for i in range(5):
        for d in range(6):
            for t in range(data.cantidad_trabajadores):
                for o in range(data.cantidad_ordenes):
                    indices = [int(data.indices_Kido[i,d,o]), int(data.indices_Xidto[i,d,t,o])]
                    values = [1, -1]
                    row = [indices, values]
                    my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])

    """ R5 """
    # Si ningun trabajador esta asignado a la orden o el turno i del dia d, ese día la orden no está tomada
    for i in range(5):
        for d in range(6):
            for o in range(data.cantidad_ordenes):
                indices = [int(data.indices_Kido[i,d,o])] + list(map(int,data.indices_Xidto[i,d,:,o].flatten()))
                values = [1] + [-1] * data.cantidad_trabajadores
                row = [indices, values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[0])

    """ R6 """
    # Un trabajador puede trabajar como mucho 4 turnos en un día
    for d in range(6):
        for t in range(data.cantidad_trabajadores):
            indices = list(map(int, data.indices_Xidto[:,d,t,:].flatten()))
            values = [1] * 5*data.cantidad_ordenes
            row = [indices, values]
            my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[4])


    ######################################################
    """ Trabajadores no pueden trabajar todos los días """
    ######################################################

    """ R7 """
    # Si el trabajador t tuvo algún turno el día d, trabajó ese día
    for i in range(5):
        for d in range(6):
            for t in range(data.cantidad_trabajadores):
                indices = [int(data.indices_Ldt[d,t])] + list(map(int, data.indices_Xidto[i,d,t,:].flatten()))
                values = [1] + [-1] * data.cantidad_ordenes
                row = [indices, values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])

    """ R8 """
    # Si el trabajador no tuvo ningún turno el día d, ese día no trabajó
    for d in range(6):
        for t in range(data.cantidad_trabajadores):
            indices = [int(data.indices_Ldt[d,t])] + list(map(int, data.indices_Xidto[:,d,t,:].flatten()))
            values = [1] + [-1] * 5*data.cantidad_ordenes
            row = [indices, values]
            my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[0])

    """ R9 """
    # El trabajador trabaja como mucho 5 días
    for t in range(data.cantidad_trabajadores):
        indices = list(map(int, data.indices_Ldt[:,t].flatten()))
        values = [1] * 6
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[5])


    ############################
    """ Ordenes Correlativas """
    ############################
    
    """ R10 & R11 """
    # Si son correlativas, o se hacen ambas o no se hace ninguna
    if len(data.ordenes_correlativas) > 0:
        for correlativas in data.ordenes_correlativas:
            indices = correlativas
            values = [1, -1]
            row = [indices, values]
            my_problem.linear_constraints.add(lin_expr=[row], senses=['E'], rhs=[0])
        
        # Si se hacen, tienen que ser inmediatamente
        # Quizás esta hace que la anterior quede redundante
        for correlativas in data.ordenes_correlativas:
            for i in range(5-1):
                for d in range(6):
                    indices = [int(data.indices_Kido[i,d,correlativas[0]])] + [int(data.indices_Kido[i+1,d,correlativas[1]])]
                    values = [1, -1]
                    row = [indices, values]
                    my_problem.linear_constraints.add(lin_expr=[row], senses=['E'], rhs=[0])


    ######################################
    """ Ordenes Conflictivas - Lejanas """
    ######################################

    """ R12 & R13 """
    # Un trabajador no puede hacer dos conflictivas de corrido - aplica en ambos sentidos
    if len(data.ordenes_conflictivas) > 0:
        for conflictivas in data.ordenes_conflictivas:
            for i in range(5-1):
                for d in range(6):
                    for t in range(data.cantidad_trabajadores):
                        indices = [int(data.indices_Xidto[i,d,t,conflictivas[0]])] + [int(data.indices_Xidto[i+1,d,t,conflictivas[1]])]
                        values = [1,1]
                        row = [indices, values]
                        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])

                        indices = [int(data.indices_Xidto[i,d,t,conflictivas[1]])] + [int(data.indices_Xidto[i+1,d,t,conflictivas[0]])]
                        values = [1,1]
                        row = [indices, values]
                        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])


    #########################################
    """ Diferencias en ordenes trabajadas """
    #########################################

    """ R14 """
    # Hago que las Et representen la cantidad de órdenes tomadas por cada trabajador
    for t in range(data.cantidad_trabajadores):
        indices = [int(data.indices_Et[t])] + list(map(int, data.indices_Xidto[:,:,t,:].flatten()))
        values = [1] + [-1] * 5*6*data.cantidad_ordenes
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['E'], rhs=[0])

    """ R15 """
    # La diferencia no puede superar 10
    for ti in range(data.cantidad_trabajadores):
        for tj in range(ti, data.cantidad_trabajadores):
            if ti != tj:
                indices = [int(data.indices_Et[ti]), int(data.indices_Et[tj])]
                values = [1, -1]
                row = [indices, values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[10])


    # """ Salarios - Lineal a Trozos """

    """ R16 """
    # La cantidad de órdenes totales de cada trabajador se descompone en la suma de sus franjas
    for t in range(data.cantidad_trabajadores):
        indices = [int(data.indices_Et[t])] + list(map(int, data.indices_salarios[:,t].flatten()))
        values = [1] + [-1]*4
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['E'], rhs=[0])

    """ ALTN 1 """
    # for t in range(data.cantidad_trabajadores):
    #     # Entre 0 y 5
    #     indices = [int(data.indices_salarios[0,t]), int(data.indices_Wt[0,t])]
    #     values = [1, -5]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])

    #     indices = [int(data.indices_salarios[0,t])]
    #     values = [1]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[5])

    #     # Entre 6 y 10
    #     indices = [int(data.indices_salarios[1,t]), int(data.indices_Wt[1,t])]
    #     values = [1, -5]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])

    #     indices = [int(data.indices_salarios[1,t]), int(data.indices_Wt[0,t])]
    #     values = [1, -5]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[0])

    #     # Entre 11 y 15
    #     indices = [int(data.indices_salarios[2,t]), int(data.indices_Wt[2,t])]
    #     values = [1, -5]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['G'], rhs=[0])

    #     indices = [int(data.indices_salarios[2,t]), int(data.indices_Wt[1,t])]
    #     values = [1, -5]
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[0])

    #     # De 16 en adelante
    #     indices = [int(data.indices_salarios[3,t]), int(data.indices_Wt[2,t])]
    #     values = [1, -30] # Big M
    #     row = [indices, values]
    #     my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[0])

    """ ALTN 2 """
    # Solo funciona si no nos preocupamos en que se llenen las últimas (de eso se encarga la función objetivo)
    for t in range(data.cantidad_trabajadores):
        indices = [int(data.indices_salarios[0,t])]
        values = [1]
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[5])

        indices = [int(data.indices_salarios[1,t])]
        values = [1]
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[5])

        indices = [int(data.indices_salarios[2,t])]
        values = [1]
        row = [indices, values]
        my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[5])

    """ R17 """
    # Conflictos entre trabajadores

    if len(data.conflictos_trabajadores) > 0:
        for conflicto in data.conflictos_trabajadores:
            for o in range(data.cantidad_ordenes):
                indices = list(map(int,(data.indices_Xidto[:,:,conflicto[0],o]).flatten())) + list(map(int,(data.indices_Xidto[:,:,conflicto[1],o]).flatten()))
                values = [1] * 5*6*2
                row = [indices, values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])

    """ R18 """
    # Órdenes Repetitivas

    if len(data.ordenes_repetitivas) > 0:
        for repetitivas in data.ordenes_repetitivas:
            for t in range(data.cantidad_trabajadores):
                indices = list(map(int, data.indices_Xidto[:,:,t,repetitivas[0]].flatten())) + list(map(int, data.indices_Xidto[:,:,t,repetitivas[1]].flatten()))
                values = [1] * 5*6*2
                row = [indices, values]
                my_problem.linear_constraints.add(lin_expr=[row], senses=['L'], rhs=[1])


def populate_by_row(my_problem, data):

    # Definimos y agregamos las variables.

    # Ben_1 + ... + Ben_10 - 1000 (*n_trabajadores) - 1200 (*n_trabajadores) - ... - 1500 (*n_trabajadores)
    data.indices_D = my_problem.variables.add(
        names = ['_D_' + str(i) for i in range(data.cantidad_ordenes)],
        obj = [orden.beneficio for orden in data.ordenes],
        lb = [0]*data.cantidad_ordenes,
        ub = [1]*data.cantidad_ordenes,
        types = ['B']*data.cantidad_ordenes
        )

    indices_salarios = my_problem.variables.add(
        names = ['_X_'+str(i)+'_'+str(wage) for wage in [1000,1200,1400,1500] for i in range(data.cantidad_trabajadores)],
        obj = sum([[-wage]*data.cantidad_trabajadores for wage in [1000, 1200, 1400, 1500]], []),
        lb = [0] * 4*data.cantidad_trabajadores,
        ub = [30] * 4*data.cantidad_trabajadores,
        types = ['I'] * 4*data.cantidad_trabajadores
    )
    # Guardo hora salario -> trabajador t
    data.indices_salarios = np.reshape(np.array(indices_salarios), (4, data.cantidad_trabajadores))

    # Variables principales, trabajador t en orden o en turno i del día d
    indices_Xidto = my_problem.variables.add(
        names = ['_X_' + str(i) + '_' + str(d) + '_' + str(t) + '_' + str(o) \
            for i in range(5) for d in range(6) for t in range(data.cantidad_trabajadores) for o in range(data.cantidad_ordenes)],
        lb = [0] * 5*6*data.cantidad_trabajadores*data.cantidad_ordenes,
        ub = [1] * 5*6*data.cantidad_trabajadores*data.cantidad_ordenes,
        types = ['B'] * 5*6*data.cantidad_trabajadores*data.cantidad_ordenes
    )
    # Guardo turno -> dia -> trabajador - orden
    data.indices_Xidto = np.reshape(np.array(indices_Xidto), (5, 6, data.cantidad_trabajadores, data.cantidad_ordenes))

    # Orden o se hace en el turno i del día d
    indices_Kido = my_problem.variables.add(
        names = ['_K_' + str(i) + '_' + str(d) + '_' + str(o) for i in range(5) for d in range(6) for o in range(data.cantidad_ordenes)],
        lb = [0] * 5*6*data.cantidad_ordenes,
        ub = [1] * 5*6*data.cantidad_ordenes,
        types = ['B'] * 5*6*data.cantidad_ordenes,
    )
    data.indices_Kido = np.reshape(np.array(indices_Kido), (5, 6, data.cantidad_ordenes))

    # El trabajador t trabajó el día d
    indices_Ldt = my_problem.variables.add(
        names = ['_L_' + str(d) + '_' + str(t) for d in range(6) for t in range(data.cantidad_trabajadores)],
        lb = [0] * 6*data.cantidad_trabajadores,
        ub = [1] * 6*data.cantidad_trabajadores,
        types = ['B'] * 6*data.cantidad_trabajadores,
    )
    data.indices_Ldt = np.reshape(np.array(indices_Ldt), (6, data.cantidad_trabajadores))

    # Ordenes totales que toma un trabajador en la semana
    data.indices_Et = my_problem.variables.add(
        names = ['_E_' + str(t) for t in range(data.cantidad_trabajadores)],
        lb = [0] * data.cantidad_trabajadores,
        ub = [30] * data.cantidad_trabajadores,
        types = ['I'] * data.cantidad_trabajadores,
    )

    # Para indicar si un trabajador saturó un rango de horas
    # indices_Wt = my_problem.variables.add(
    #     names = ['_w_' + r + '_' + str(t) for r in ['0_5', '6_10', '11_15'] for t in range(data.cantidad_trabajadores)],
    #     lb = [0] * 3*data.cantidad_trabajadores,
    #     ub = [1] * 3*data.cantidad_trabajadores,
    #     types = ['B'] * 3*data.cantidad_trabajadores,
    # )

    # data.indices_Wt = np.reshape(np.array(indices_Wt), (3, data.cantidad_trabajadores))

    #my_problem.variables.add(obj = coeficientes_funcion_objetivo, lb = lbs, ub = ubs, types= types)

    # Seteamos direccion del problema
    my_problem.objective.set_sense(my_problem.objective.sense.maximize)
    # ~ my_problem.objective.set_sense(my_problem.objective.sense.minimize)

    # Definimos las restricciones del modelo. Encapsulamos esto en una funcion.
    add_constraint_matrix(my_problem, data)

    # Exportamos el LP cargado en myprob con formato .lp.
    # Util para debug.
    my_problem.write('balanced_assignment.lp')

def solve_lp(my_problem, data):

    # Resolvemos el ILP.

    my_problem.solve()

    # Obtenemos informacion de la solucion. Esto lo hacemos a traves de 'solution'.
    x_variables = np.array(my_problem.solution.get_values())
    objective_value = my_problem.solution.get_objective_value()
    status = my_problem.solution.get_status()
    status_string = my_problem.solution.get_status_string(status_code = status)

    print('Funcion objetivo: ',objective_value)
    print('Status solucion: ',status_string,'(' + str(status) + ')')

    # Imprimimos las variables usadas.

    used_idx = x_variables > TOLERANCE
    tags = np.array(my_problem.variables.get_names())[ used_idx ]
    used_vars = x_variables[ used_idx ]
    log = dict(zip(tags, used_vars))

    f = open('log.txt', 'w')
    for key, value in log.items():
        f.write('%s: %s\n' % (key, value))
    f.close()


    # for i in range(len(x_variables)):
    #     # Tomamos esto como valor de tolerancia, por cuestiones numericas.
    #     if x_variables[i] > TOLERANCE:
    #         #print('x_' + str(data.items[i].index) + ':' , x_variables[i])
    #         print(x_variables[i])

def main():

    # Obtenemos los datos de la instancia.
    data = get_instance_data()
    # ~ print(vars(data))
    # ~ for orden in data.ordenes:
        # ~ print(vars(orden))
    #return

    # Definimos el problema de cplex.
    prob_lp = cplex.Cplex()

    # Armamos el modelo.
    populate_by_row(prob_lp,data)

    # Resolvemos el modelo.
    solve_lp(prob_lp,data)


if __name__ == '__main__':
    main()
