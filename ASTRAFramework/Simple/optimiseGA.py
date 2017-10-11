from ASTRAInjector import *
import numpy as np
from constraints import *
import os
import read_astra_file as raf
from deap import algorithms
from deap import base
from deap import creator
from deap import tools
import operator
import random
import multiprocessing
import csv


import shutil
import uuid
class TemporaryDirectory(object):
    """Context manager for tempfile.mkdtemp() so it's usable with "with" statement."""

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def tempname(self):
        return 'tmp'+str(uuid.uuid4())

    def __enter__(self, dir=os.getcwd()):
        exists = True
        while exists:
            self.name = dir + '/' + self.tempname()
            if not os.path.exists(self.name):
                exists=False
                os.makedirs(self.name)
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)

class fitnessFunc():

    def __init__(self, args, tempdir, npart=250, ncpu=3):
        self.tmpdir = tempdir
        linac1field, linac1phase, linac2field, linac2phase, linac3field, linac3phase, fhcfield, fhcphase, linac4field, linac4phase = args
        self.parameters = args
        self.linacfields = [linac1field, linac2field, linac3field, linac4field]
        self.dirname = os.path.basename(self.tmpdir)
        astra = ASTRAInjector(self.dirname, overwrite=True)
        if not os.name == 'nt':
            astra.defineASTRACommand(['mpiexec','-np',str(ncpu),'/opt/ASTRA/astra_MPICH2_Quiet.sh'])
        astra.loadSettings('short_240.settings')
        astra.modifySetting('linac1_field', abs(linac1field))
        astra.modifySetting('linac1_phase', linac1phase)
        astra.modifySetting('linac2_field', abs(linac2field))
        astra.modifySetting('linac2_phase', linac2phase)
        astra.modifySetting('linac3_field', abs(linac3field))
        astra.modifySetting('linac3_phase', linac3phase)
        astra.modifySetting('4hc_field', abs(fhcfield))
        astra.modifySetting('4hc_phase', fhcphase)
        astra.modifySetting('linac4_field', abs(linac4field))
        astra.modifySetting('linac4_phase', linac4phase)
        astra.createInitialDistribution(npart=npart, charge=250)
        astra.applySettings()
        astra.runASTRAFiles()
        ft = feltools(self.dirname)
        sddsfile = ft.convertToSDDS('test.in.128.4929.128')
        self.cons = constraintsClass()

    def emittance(self, x, xp, p):
        x = x - np.mean(x)
        xp = xp - np.mean(xp)
        gamma = np.mean(p)/511000
        return gamma*np.sqrt(np.mean(x**2)*np.mean(xp**2) - np.mean(x*xp)**2)

    def calculateBeamParameters(self):
        beam = raf.read_astra_beam_file(self.dirname+'/test.in.128.4929.128')
        sigmat = 1e12*np.std(beam['t'])
        sigmap = np.std(beam['p'])
        meanp = np.mean(beam['p'])
        emitx = 1e6*self.emittance(beam['x'],beam['xp'],beam['p'])
        emity = 1e6*self.emittance(beam['y'],beam['yp'],beam['p'])
        fitp = 100*sigmap/meanp
        fhcfield = self.parameters[6]

        constraintsList = {
        'lessThan': {'value': sigmat, 'limit': 0.25, 'weight': 4},
        'lessThan': {'value': fitp, 'limit': 0.5, 'weight': 1},
        'greaterThan': {'value': meanp, 'limit': 200, 'weight': 2},
        'lessThan': {'value': max(self.linacfields), 'limit': 32, 'weight': 5},
        'lessThan': {'value': self.parameters[6], 'limit': 35, 'weight': 5},
        'lessThan': {'value': emitx, 'limit': 1, 'weight': 3},
        'lessThan': {'value': emity, 'limit': 1, 'weight': 3},
        }
        fitness = self.cons.constraints(constraintsList)
        return fitness

def optfunc(args, dir=None, **kwargs):
    if dir == None:
        with TemporaryDirectory(dir=os.getcwd()) as tmpdir:
            fit = fitnessFunc(args, tmpdir, **kwargs)
            fitvalue = fit.calculateBeamParameters()
    else:
            fit = fitnessFunc(args, dir, **kwargs)
            fitvalue = fit.calculateBeamParameters()
    return (fitvalue,)

best = [14.95092614,-21.06732049,31.23925726,-24.8609014,0,0,20.44109707,144.3601313,16.86181033,15.40806285]

# print optfunc(best, dir=os.getcwd()+'/test', npart=10000, ncpu=20)

startranges = [[10, 32], [-30,30], [10, 32], [-30,30], [10, 32], [-30,30], [10, 32], [135,200], [10, 32], [-30,30]]

def generate():
    return creator.Individual(random.uniform(a,b) for a,b in startranges)

# print generate()

creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Attribute generator
toolbox.register("attr_bool", generate)

# Structure initializers
toolbox.register("Individual", generate)
toolbox.register("population", tools.initRepeat, list, toolbox.Individual)

toolbox.register("evaluate", optfunc)
toolbox.register("mate", tools.cxBlend, alpha=0.2)
toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=3, indpb=0.3)
toolbox.register("select", tools.selTournament, tournsize=3)


if __name__ == "__main__":
    random.seed(64)

    # Process Pool of 4 workers
    if not os.name == 'nt':
        pool = multiprocessing.Pool(processes=10)
    else:
        pool = multiprocessing.Pool(processes=6)
    toolbox.register("map", pool.map)
    # toolbox.register("map", futures.map)

    if not os.name == 'nt':
        pop = toolbox.population(n=100)
    else:
        pop = toolbox.population(n=18)
    hof = tools.HallOfFame(10)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean)
    stats.register("std", numpy.std)
    stats.register("min", numpy.min)
    stats.register("max", numpy.max)

    pop, logbook = algorithms.eaSimple(pop, toolbox, cxpb=0.5, mutpb=0.2, ngen=20,
                            stats=stats, halloffame=hof)

    # print 'pop = ', pop
    print logbook
    print hof

    with open('best_solutions.csv','wb') as out:
        csv_out=csv.writer(out)
        for row in hof:
            csv_out.writerow(row)
    pool.close()

    print 'best fitness = ', optfunc(hof[0], dir=os.getcwd()+'/best', npart=10000, ncpu=20)
