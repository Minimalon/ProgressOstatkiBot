# @ProgressOstatki_bot
Высылает последние сгенерированные остатки или список из последних 6 сгенерированных остатков.

Генерирует штрихкод Code128 - нужно выбрать тип товара (т.е отдел), затем если выбрать 1-3 отдел бот запросит ШК и имя товара (имя товара не должен быть длиннее 35 символов). Если выбрать 4 отдел, то ШК вводить не нужно, бот сам сгенерирует ШК в следующем формате:

      # Приходит номер компа. Приходят с дефизом. Например "1798-1".
      def get_valid_barcode(pcNumber):
            # Берем только до дефиза,то есть только номер компьютера. С 1798-1 станет 1798
            barcode = pcNumber.split('-')[0]
            pcNumber = pcNumber.split('-')[0]  
            # количество символов в номере компьютера. Например в "1798" 4 символа.
            if len(pcNumber) == 1:
                   # Прибавляем нули к штрихкоду
                  barcode += "000000"  
            if len(pcNumber) == 2:
                  barcode += "00000"
            if len(pcNumber) == 3:
                  barcode += "0000"
            if len(pcNumber) == 4:
                  barcode += "000"
            # Количество до этого сгенерированных штрихкодов
            count_busy_barcode = [barcode for line in open(config.dir_path + 'logs/busy_barcode.txt', 'r') if re.search(barcode, line)] 
            with open(config.dir_path + 'logs/busy_barcode.txt', 'a') as file:
                  barcode = barcode + str(len(count_busy_barcode))
                  file.write(str(barcode) + '\n')
            return str(barcode)


Если номер компьютера "123" генерирует первый раз ШК, то его ШК будет 12300001, второй раз 12300002 и так далее.  

# Файлы
***function.py*** - Все основные функции  
***cashInfo.py*** - Файл для хранения глобальных переменных  
***main.py*** - основная логика  
***Ermilov-bold.otf*** - Шрифт на картинке со штрихкодом  
***bacode.png*** - Картинка штрихкода  
***busy_barcode.txt*** - все занятые штрихкоды  
***debug.log*** - Логи бота  
