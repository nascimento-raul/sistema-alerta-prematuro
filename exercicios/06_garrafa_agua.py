

texto = """Escolha sua água para comprar
(1) Água mineral sem gás
(2) àgua mineral com gás
 """


opcao = input (texto)
conta = 0

if opcao == "1":
    conta = 1.5 ###("Sua conta deu: R$ 1,50")

elif opcao == "2":
    conta = 2.5 ##print("Sua conta deu: R$ 2,50")

if conta == 0:
    print ("Entre com uma opção correta, por favor")

else:
    print ("Sua conta é: R$", conta)