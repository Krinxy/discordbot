import re


class SlotNaming:
    @staticmethod
    def name_for_slot(slot, name_pool):
        cycle, pool_index = divmod(slot, len(name_pool))
        name = name_pool[pool_index]
        return name if cycle == 0 else f"{name} {cycle + 1}"

    @staticmethod
    def slot_from_name(name, name_pool):
        escaped = "|".join(re.escape(entry) for entry in name_pool)
        match = re.fullmatch(rf"({escaped})(?: (\d+))?", name)
        if match is None:
            return None
        pool_index = name_pool.index(match.group(1))
        if match.group(2) is None:
            cycle = 0
        else:
            cycle_number = int(match.group(2))
            if cycle_number < 2:
                return None
            cycle = cycle_number - 1
        return cycle * len(name_pool) + pool_index

    @staticmethod
    def next_free_slot(occupied_slots, name_pool, max_generic_channels):
        for slot in range(max_generic_channels):
            if slot not in occupied_slots:
                return slot
        return None
