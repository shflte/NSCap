from mininet.topo import Topo

class Topo1( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        H1 = self.addHost( 'h1' )
        H2 = self.addHost( 'h2' )
        H3 = self.addHost( 'h3' )
        H4 = self.addHost( 'h4' )

        S1 = self.addSwitch( 's1' )

        self.addLink( S1, H1 )
        self.addLink( S1, H2 )
        self.addLink( S1, H3 )
        self.addLink( S1, H4 )

class Topo2( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        H5 = self.addHost( 'h5' )
        H6 = self.addHost( 'h6' )
        H7 = self.addHost( 'h7' )
        H8 = self.addHost( 'h8' )

        S2 = self.addSwitch( 's2' )

        self.addLink( S2, H5 )
        self.addLink( S2, H6 )
        self.addLink( S2, H7 )
        self.addLink( S2, H8 )


topos = {
    'topo1': ( lambda: Topo1() ),
    'topo2': ( lambda: Topo2() )
}
