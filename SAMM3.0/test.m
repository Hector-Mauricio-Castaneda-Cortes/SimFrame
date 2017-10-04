clear
drift1 = Drift;
drift1.length = 1.5;
quad1 = Quadrupole;
quad1.length = 0.3;
quad1.gradient = 0.8;
beamline1 = Beamline;
beamline1.componentlist = {quad1,drift1};
beam1 = Beam(Positron);
beam1.energy = 1.20*PhysicalUnits.GeV;
ptcle1 = [0.001,0,0,0,0,0]';
ptcle2 = [0,0,0.001,0,0,0]';
beam1.particles = [ptcle1 ptcle2];
beam2 = beamline1.Track([1 2],beam1);
beam2.particles 
beam2 = beamline1.Track([1 2],beam1);
beam2.particles
beam2 = beamline1.Track([1 2],beam1);
beam2.particles