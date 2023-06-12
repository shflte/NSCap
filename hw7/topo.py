from mininet.topo import Topo

class Topo1( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        H1 = self.addHost('h1', ip='10.0.0.1/24')
        H2 = self.addHost('h2', ip='10.0.0.2/24')
        H3 = self.addHost('h3', ip='10.0.0.3/24')
        H4 = self.addHost('h4', ip='10.0.0.4/24')

        S1 = self.addSwitch( 's1' )

        self.addLink( S1, H1 )
        self.addLink( S1, H2 )
        self.addLink( S1, H3 )
        self.addLink( S1, H4 )

class Topo2( Topo ):
    "Simple topology example."

    def build( self ):
        "Create custom topo."

        H5 = self.addHost('h5', ip='10.0.0.5/24')
        H6 = self.addHost('h6', ip='10.0.0.6/24')
        H7 = self.addHost('h7', ip='10.0.0.7/24')
        H8 = self.addHost('h8', ip='10.0.0.8/24')

        S2 = self.addSwitch( 's2' )

        self.addLink( S2, H5 )
        self.addLink( S2, H6 )
        self.addLink( S2, H7 )
        self.addLink( S2, H8 )


topos = {
    'topo1': ( lambda: Topo1() ),
    'topo2': ( lambda: Topo2() )
}
