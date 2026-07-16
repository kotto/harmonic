
'use strict';
const K={txt:'',shift:false,lock:false,ts:0,alt:false,voice:false,vt:null,emo:false};
const KR=[[['1','~'],['2','@'],['3','#'],['4','$'],['5','%'],['6','^'],['7','&'],['8','*'],['9','('],['0',')']],[['a','à'],['z','æ'],['e','€'],['r','®'],['t','™'],['y','¥'],['u','ù'],['i','ï'],['o','œ'],['p','°']],[['q',''],['s','ß'],['d',''],['f',''],['g',''],['h',''],['j',''],['k',''],['l',''],['m','µ']],[['w',''],['x',''],['c','ç'],['v',''],['b',''],['n','ñ']]];
const EM=['😊','😂','❤️','🔥','✨','🙏','👍','🎉','😄','😍','🤔','😎','🥰','💪','🙌','👋','🎶','🌟','💡','🚀','🌍','🍕','☕','🎯','💬','✅','😘','🫶','🤩','😅','🫠','🤝','🌸','⭐','🎵'];
const SD={'':['Sophie','Appeler','Réunion','Oui','Super','Merci','Demain'],'so':['Sophie','Soirée','Souvenir'],'ap':['Appeler','Appelle','Après'],'me':['Merci','Message','Même'],'ou':['Oui','Ouvert','Ouais'],'to':['Tokyo','Toi','Toujours'],'de':['Demain','Décision','Depuis'],'re':['Réunion','Rendez-vous','Retrouve'],'su':['Super','Sur','Surtout'],'bi':['Bientôt','Bien','Bises'],'bo':['Bonjour','Bonsoir','Bon'],'co':['Comment','Comme','Contact'],'pr':['Prépare','Prendre','Prochain'],'pa':['Paris','Parfait','Partager'],'ma':['Maintenant','Matin','Mais'],'vo':['Voici','Voilà','Voyage'],'sa':['Salut','Samedi','Sans'],'tr':['Très','Travail','Trouver']};
	const RP=['Je suis KA, votre assistant personnel intelligent. Posez-moi une question !','Que voulez-vous savoir ? Je suis là pour vous aider.','Bonjour ! Je suis KA. Que puis-je faire pour vous ?'];
	// Note : RP n'est utilisé qu'en mode déconnecté temporaire
	
