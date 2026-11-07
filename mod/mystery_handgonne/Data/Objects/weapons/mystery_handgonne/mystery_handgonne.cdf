<?xml version="1.0" encoding="us-ascii"?>
<!-- Vanilla crossbow skeleton (a copied .chr gets no animations: its chrparams is never applied, see
     docs/DEVLOG.md) with the gun body as CA_SKIN. The Arrow attachment is the vanilla one:
     the game snaps the ammo to bone Crossbow_arrow and ignores offsets, so the round itself is invisible
     (mystery_handgonne_round.cgf). Gun body: Henry Lever-Action Rifle by Zverev Kirill, CC BY 4.0.
     (A class 13 / hand_cannon.chr version was tried and dropped: the handgonne aiming did not work for this gun.) -->
<CharacterDefinition>
  <Model File="objects/manmade/weapons/crossbows/crossbow.chr" Material="objects/characters/nodraw" />
  <AttachmentList>
    <Attachment Type="CA_BONE" AName="Arrow" Rotation="0.99999994,0,0,0" Position="0,0,0" BoneName="Crossbow_arrow" Flags="0" />
    <Attachment Type="CA_SKIN" AName="mystery_handgonne" Binding="objects/weapons/mystery_handgonne/mystery_handgonne.skin" Material="objects/weapons/mystery_handgonne/mystery_handgonne.mtl" Flags="0" />
  </AttachmentList>
</CharacterDefinition>
