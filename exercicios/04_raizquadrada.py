numero = input ("Entre com um numero inteiro para calcular a raiz: ")
numero = int (numero)

raiz = numero ** (1/2) # numero ** 0.5
raiz = round (raiz, 2)

print ("Raiz quadrada de", numero,"é: ", raiz)

