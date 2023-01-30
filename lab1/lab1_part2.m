V1 = 10; %test inputs for the problem
R1 = 10;
R2 = 20;
R3 = 40;
R4 = 20; % I know the answer to this is going to 10/30 amps

R_EQ = R1 + 1/(1/R3 + 1/(R2+R4)); %applying resistor rules

I_R1 = V1/R_EQ; %By Ohm's Law
V_R1 = R1*I_R1; %voltage drop over R1 by Ohm's Law
V_R3 = V1 - V_R1; %voltage drop over R3 by KVL
I_R3 = V_R3/R3; % by Ohm's law
I_R2 = I_R1-I_R3; %by KCL
I_R4 = I_R2; % by KCL

% once you know the currents, the power is i^2*R
P_R1 = I_R1^2 * R1; 
P_R2 = I_R2^2 * R2;
P_R3 = I_R3^2 * R3;
P_R4 = I_R4^2 * R4;

fprintf("Currents = %.2f,%.2f,%.2f,%.2f\n",I_R1,I_R2,I_R3,I_R4);
fprintf("Powers = %.2f,%.2f,%.2f,%.2f\n",P_R1,P_R2,P_R3,P_R4);
bar([P_R1,P_R2,P_R3,P_R4])
xticklabels(["R1","R2","R3","R4"])
xlabel("resistors")
ylabel("power (watts)")

