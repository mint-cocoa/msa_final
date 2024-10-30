class FacilityNode:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Facility({self.name})"

class TicketTypeNode:
    def __init__(self, name):
        self.name = name
        self.facilities = []  # 각 티켓 타입이 허용하는 시설 목록

    def add_facility(self, facility):
        self.facilities.append(facility)

    def __repr__(self):
        return f"TicketType({self.name})"

class ParkNode:
    def __init__(self, name):
        self.name = name
        self.ticket_types = []  # 공원의 티켓 종류 목록

    def add_ticket_type(self, ticket_type):
        self.ticket_types.append(ticket_type)

    def __repr__(self):
        return f"Park({self.name})"

# 트리 구조를 출력하는 함수
def print_tree(park):
    print(f"{park}")
    for ticket_type in park.ticket_types:
        print(f"  {ticket_type}")
        for facility in ticket_type.facilities:
            print(f"    {facility}")

# 예시 트리 구성
if __name__ == "__main__":
    # 공원 생성
    main_park = ParkNode("Wonderland Park")

    # 티켓 종류 생성
    vip_ticket = TicketTypeNode("VIP Ticket")
    regular_ticket = TicketTypeNode("Regular Ticket")

    # 시설 생성 및 할당
    roller_coaster = FacilityNode("Roller Coaster")
    ferris_wheel = FacilityNode("Ferris Wheel")
    haunted_house = FacilityNode("Haunted House")

    # VIP 티켓이 접근할 수 있는 시설
    vip_ticket.add_facility(roller_coaster)
    vip_ticket.add_facility(ferris_wheel)
    vip_ticket.add_facility(haunted_house)

    # Regular 티켓이 접근할 수 있는 시설
    regular_ticket.add_facility(ferris_wheel)

    # 공원에 티켓 타입 추가
    main_park.add_ticket_type(vip_ticket)
    main_park.add_ticket_type(regular_ticket)

    # 트리 출력
    print_tree(main_park)
