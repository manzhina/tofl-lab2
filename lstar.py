from collections import defaultdict
import itertools

class ObservationTable:
    """
    Представляет таблицу наблюдений для алгоритма L*, управляет множествами S (префиксы) и E (суффиксы),
    а также таблицей T, где записаны результаты запросов о принадлежности для каждого (S и SA)*E к языку
    """
    def __init__(self, alphabet, membership_query):
        self.S = {''}          
        self.E = {''}          
        self.alphabet = alphabet
        self.T = defaultdict(dict) 
        self.orig_membership_query = membership_query
        self.populate_initial_table()

    def wrapped_membership_query(self, word):
        """Попытка оптимизировать число запросов, мб лишняя..."""
        if self.T.get(word, {}).get('') is not None:
            return self.T[word]['']
        else:
            return self.orig_membership_query(word)

    def populate_initial_table(self):
        """
        Заполняет таблицу наблюдений, делая запросы о принадлежности для всех комбинаций в S * E и (SA) * E.
        """
        for s in sorted(self.S):
            for e in sorted(self.E):
                if e not in self.T[s]:
                    self.T[s][e] = self.wrapped_membership_query(s + e)
            for a in sorted(self.alphabet):
                sa = s + a
                for e in list(self.E):
                    if e not in self.T[sa]:
                        self.T[sa][e] = self.wrapped_membership_query(sa + e)

    def is_closed(self):
        """
        Проверяет, замкнута ли таблица. Если не замкнута, возвращает (False, контрпример).
        """
        sorted_E = sorted(self.E)
        for s in sorted(self.S):
            for a in sorted(self.alphabet):
                sa = s + a
                row_sa = tuple(self.T[sa][e] for e in sorted_E)
                for s_prime in self.S:
                    row_s_prime = tuple(self.T[s_prime][e] for e in sorted_E)
                    if row_sa == row_s_prime:
                        break
                else:
                    return False, sa
        return True, None

    def is_consistent(self):
        """
        Проверяет, согласована ли таблица. Если не согласована, возвращает (False, новый суффикс для добавления в E).
        """
        sorted_E = sorted(self.E)
        rows = {s: tuple(self.T[s][e] for e in sorted_E) for s in self.S}
        s_list = sorted(self.S)
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                s1, s2 = s_list[i], s_list[j]
                if rows[s1] == rows[s2]:
                    for a in sorted(self.alphabet):
                        sa1 = s1 + a
                        sa2 = s2 + a
                        row_sa1 = tuple(self.T.get(sa1, {}).get(e, self.wrapped_membership_query(sa1 + e)) for e in sorted_E)
                        row_sa2 = tuple(self.T.get(sa2, {}).get(e, self.wrapped_membership_query(sa2 + e)) for e in sorted_E)
                        if row_sa1 != row_sa2:
                            for idx, (v1, v2) in enumerate(zip(row_sa1, row_sa2)):
                                if v1 != v2:
                                    new_suffix = a + sorted_E[idx]
                                    return False, new_suffix
        return True, None

    def add_suffix(self, new_e):
        """
        Добавляет новый суффикс в E и обновляет таблицу.
        """
        self.E.add(new_e)
        for s in self.S.copy():
            if new_e not in self.T[s]:
                self.T[s][new_e] = self.wrapped_membership_query(s + new_e)
            for a in sorted(self.alphabet):
                sa = s + a
                if new_e not in self.T[sa]:
                    self.T[sa][new_e] = self.wrapped_membership_query(sa + new_e)

    def add_prefix(self, new_s):
        """
        Добавляет новый префикс в S и обновляет таблицу.
        """
        self.S.add(new_s)
        for e in sorted(self.E.copy()):
            if e not in self.T[new_s]:
                self.T[new_s][e] = self.wrapped_membership_query(new_s + e)
        for a in sorted(self.alphabet):
            sa = new_s + a
            for e in sorted(self.E.copy()):
                if e not in self.T[sa]:
                    self.T[sa][e] = self.wrapped_membership_query(sa + e)

    def get_equivalence_classes(self):
        """
        Строит классы эквивалентности по текущим строкам в S.
        Возвращает словарь, в котором каждому представителю класса сопоставлен ID класса.
        Видимо не нужно на самом деле
        """
        sorted_E = sorted(self.E)
        rows = {s: tuple(self.T[s][e] for e in sorted_E) for s in self.S}
        classes = {}
        class_id = 0
        row_to_class = {}
        for s in sorted(self.S):
            r = rows[s]
            if r not in row_to_class:
                row_to_class[r] = class_id
                class_id += 1
            classes[s] = row_to_class[r]
        return classes

    def get_language_membership(self):
        """
        Строит по классам эквивалентности словарь "самый короткий представитель класса: принадлежность к языку"
        Видимо тоже не нужно
        """
        class_id_dict = self.get_equivalence_classes()
        grouped = {}
        for string, id in class_id_dict.items():
            if id not in grouped:
                grouped[id] = []
            grouped[id].append(string)
        shortest_strings = {}
        for id, strings in grouped.items():
            shortest_string = min(strings, key=lambda s: (len(s), s))
            shortest_strings[shortest_string] = self.T[shortest_string]['']
        return shortest_strings

    def display_table(self):
        """
        Показывает таблицу наблюдений для отладки.
        """
        sorted_S = sorted(self.S)
        sorted_E = sorted(self.E)
        print("S:", sorted_S)
        print("E:", sorted_E)
        header = [""] + list(sorted_E)
        print("\t".join(header))
        for s in sorted_S:
            row = [s] + [str(self.T[s][e]) for e in sorted_E]
            print("\t".join(row))
        print("\nS·A:")
        for s in sorted_S:
            for a in sorted(self.alphabet):
                sa = s + a
                if sa not in sorted_S:
                    row = [sa] + [str(self.T[sa][e]) for e in sorted_E]
                    print("\t".join(row))
        print("\n")

    def eq_query(self):
        """
        Функция потенциально для запроса на эквивалентность
        """
        main_prefixes = 'ε' + " ".join(sorted(self.S))
        non_main_prefixes = " ".join(
            sa for s in sorted(self.S) for a in sorted(self.alphabet) if (sa := s + a) not in self.S
        )
        suffixes = 'ε' + " ".join(sorted(self.E))

        table = " ".join(
            str(self.T[s][e]) for s in sorted(self.S) + non_main_prefixes.split() for e in sorted(self.E)
        )

        output = {
            "main_prefixes": main_prefixes,
            "non_main_prefixes": non_main_prefixes,
            "suffixes": suffixes,
            "table": table
        }
        print(output)
        response = input()
        return response

class LStar:
    """
    Реализация примитивного алгоритма L* 
    Взаимодействует с запросами о принадлежности и эквивалентности
    """
    def __init__(self, alphabet, membership_query):
        self.alphabet = alphabet
        self.membership_query = membership_query
        self.table = ObservationTable(alphabet, membership_query)

    def run(self):
        """
        Запускает алгоритм L* и работает до тех пор, пока не будет получен ответ TRUE
        """
        while True:
            closed, sa = self.table.is_closed()
            while not closed:
                print(f"Таблица не замкнута. Добавляем '{sa}' в S.")
                self.table.add_prefix(sa)
                closed, sa = self.table.is_closed()

            consistent, new_e = self.table.is_consistent()
            while not consistent:
                print(f"Таблица не согласована. Добавляем '{new_e}' в E.")
                self.table.add_suffix(new_e)
                consistent, new_e = self.table.is_consistent()

            self.table.display_table()
            # classes = self.table.get_language_membership()
            result = self.table.eq_query()
            if result == "TRUE":
                print("Обучение завершено. Построен верный автомат.")
                return 
            else:
                print(f"Контрпример получен: '{result}'")
                suffixes = [result[i:] for i in range(len(result))]
                for suff in suffixes:
                    if suff not in self.table.E:
                        print(f"Добавляем суффикс '{suff}' из контрпримера в E.")
                        self.table.add_suffix(suff)

def make_query_functions(f):
    def eq_query() -> str:
        response = f.readline().strip()
        print("eq", response)
        return response

    def mem_query(word) -> int:
        response = f.readline().strip()
        print("mem", response)
        return int(response)  

    return eq_query, mem_query

if __name__ == '__main__':
    with open('test.txt', 'r') as f:
        alphabet = set(list(f.readline().strip()))
        eq_query, mem_query = make_query_functions(f)
        lstar = LStar(alphabet=alphabet, membership_query=mem_query)
        lstar.table.eq_query = eq_query
        lstar.run()