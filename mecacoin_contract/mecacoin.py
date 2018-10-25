from iconservice import *
from datetime import date, timedelta, datetime

class mecacoin(IconScoreBase):
    _BALANCES = 'balances'
    _TOTAL_SUPPLY = 'total_supply'
    _DECIMALS = 'decimals'
    _TOKEN_RELEASE_BALANCE_TABLE = 'token_release_percent_table'
    _TOKEN_RELEASE_TIME_TABLE = 'token_release_time_table'
    _TOKEN_INVESTOR_TABLE = 'token_investor_table'
    
    _BONUS_INDEX = 12
    
    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        
        self._token_release_balance_table = DictDB(self._TOKEN_RELEASE_BALANCE_TABLE, db, value_type=int, depth=2)
        self._token_release_time_table = DictDB(self._TOKEN_RELEASE_TIME_TABLE, db, value_type=int, depth=2)
        self._token_release_investor_table = DictDB(self._TOKEN_INVESTOR_TABLE, db, value_type=int)

    def on_install(self) -> None:
        super().on_install()
        
        total_supply = 5000000000
        _decimals = 0

        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()
        
    @external(readonly=True)
    def name(self) -> str:
        return "Meca Coin"

    @external(readonly=True)
    def tokenOwner(self) -> str:
        return self.owner
        
    @external(readonly=True)
    def symbol(self) -> str:
        return "MCA"

    @external(readonly=True)
    def decimals(self) -> int:
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'

        if self.msg.sender == _to :
            revert("The recevier and sender must be different.")
            
        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        # Checks the sending value and balance.
        if _value < 0:
            revert("Transferring value cannot be less than zero")
        if self._balances[_from] < _value:
            revert("Out of balance")
            
        if self._token_release_investor_table[_from] == 1 and _to != self.owner:
            if self._getUnlockedBalance(_from) < _value:
                revert("Out of balance")
        
            # Minus the maximum allowed amount.
            s_index = -1;
            d = int(self.now() / 1000000.0)
            for _index in range(0,12):
                if self._token_release_time_table[_from][_index] < d : 
                    s_index = _index
            if s_index >= 0 and s_index <= 11 :
                self._token_release_balance_table[_from][s_index] -= _value 

        # If the sender is token holder, will be set token lock.
        if _from == self.owner :
              _data = b'From Token Holder'
              self.setDefaultLock(_to, 1)
                                        
        # Update balance.
        self._balances[_from] = self._balances[_from] - _value
        self._balances[_to] = self._balances[_to] + _value
        
    def _getUnlockedBalance(self, _to: Address) -> int:     
        t = 0
        b = 0
        d = int(self.now() / 1000000.0)
        for _index in range(0,12):
            if self._token_release_time_table[_to][_index] < d : 
                t = self._token_release_balance_table[_to][_index]

        if self._token_release_time_table[_to][self._BONUS_INDEX] < d : 
            b = self._token_release_balance_table[_to][self._BONUS_INDEX]

        if (t+b) > self._balances[_to] :
        		return self._balances[_to]

        return (t+b)
    
    @external        
    def setDefaultLock(self, _to: Address, _flag : int) -> None : 
        self._token_release_investor_table[_to] = _flag
        d = int(self.now() / 1000000.0)
        for month in range(0,13) :
            self.setLock(_to, month, d, 0 )
    
    @external
    def getNow(self) -> int:
        d = int(self.now() / 1000000.0)

        return d
                           
    @external
    def getUnlockedBalance(self, _to: Address) -> int:
        if self.msg.sender != self.owner :
            _to = self.msg.sender

        return self._getUnlockedBalance(_to)
       
    @external
    def getLockTimes(self, _to: Address) -> str:
        if self.msg.sender != self.owner :
            return "Denied"
            
        r = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        for _index in range(0,13):
            r[_index] = "{\"key\":" + str(_index) + ", \"value\": " + str(self._token_release_time_table[_to][_index]) + "}"

        return r
                 
    @external
    def getLockBalances(self, _to: Address) -> str:     
        if self.msg.sender != self.owner :
            return "Denied"
            
        r = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        for _index in range(0,13):
            r[_index] = "{\"key\":" + str(_index) + ", \"value\": " + str(self._token_release_balance_table[_to][_index]) + "}"

        return r
                
    @external
    def setLock(self, _to: Address, _index: int, _time: int, _balance: int) -> None:
        if self.msg.sender == self.owner :
            if _index >= 0 and _index <= 11 :
                self._token_release_time_table[_to][_index] = _time
                self._token_release_balance_table[_to][_index] = _balance
            if _index >= self._BONUS_INDEX :
                self._token_release_time_table[_to][self._BONUS_INDEX] = _time
                self._token_release_balance_table[_to][self._BONUS_INDEX] = _balance                
